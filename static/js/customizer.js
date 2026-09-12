(function () {
    'use strict';

    const dataNode = document.getElementById(
        'visual-customizer-data'
    );

    if (!dataNode) return;

    let initialData = {};

    try {
        initialData = JSON.parse(
            dataNode.textContent || '{}'
        );
    } catch (error) {
        initialData = {};
    }

    let rules = Array.isArray(initialData.rules)
        ? initialData.rules
        : [];

    let theme =
        initialData.theme &&
        typeof initialData.theme === 'object'
            ? initialData.theme
            : {};

    const canEdit =
        initialData.canEdit === true;

    const editRequested =
        new URLSearchParams(
            window.location.search
        ).get('visual_edit') === '1';

    const editMode =
        editRequested &&
        canEdit &&
        window.parent !== window;

    const snapshots = new Map();

    let selectedElement = null;
    let currentBreakpoint = getBreakpoint();
    let dragState = null;
    let resizeState = null;
    let editorMode = 'select';
    let suppressClickUntil = 0;

    const STYLE_KEYS = [
        'color',
        'backgroundColor',
        'fontSize',
        'fontWeight',
        'fontFamily',
        'textAlign',
        'lineHeight',
        'letterSpacing',
        'borderRadius',
        'opacity',
        'padding',
        'margin',
        'objectFit',
        'boxShadow'
    ];

    function safeSelector(value) {
        if (
            window.CSS &&
            typeof window.CSS.escape === 'function'
        ) {
            return window.CSS.escape(
                String(value)
            );
        }

        return String(value).replace(
            /[^a-zA-Z0-9_-]/g,
            ''
        );
    }

    function shortHash(value) {
        let hash = 2166136261;

        for (
            let index = 0;
            index < value.length;
            index += 1
        ) {
            hash ^= value.charCodeAt(index);
            hash = Math.imul(
                hash,
                16777619
            );
        }

        return (hash >>> 0).toString(36);
    }

    function stablePath(element) {
        const parts = [];
        let current = element;

        while (
            current &&
            current !== document.body
        ) {
            if (current.id) {
                parts.unshift(
                    `${current.tagName.toLowerCase()}#${current.id}`
                );

                break;
            }

            const parent =
                current.parentElement;

            if (!parent) break;

            const sameTags =
                Array.from(
                    parent.children
                ).filter(
                    (item) =>
                        item.tagName ===
                        current.tagName
                );

            const position =
                sameTags.indexOf(current) + 1;

            parts.unshift(
                `${current.tagName.toLowerCase()}:${position}`
            );

            current = parent;
        }

        return (
            `${window.location.pathname}|` +
            parts.join('>')
        );
    }

    function directText(element) {
        return Array.from(
            element.childNodes
        )
            .filter(
                (node) =>
                    node.nodeType ===
                        Node.TEXT_NODE &&
                    node.nodeValue.trim()
            )
            .map(
                (node) =>
                    node.nodeValue.trim()
            )
            .join(' ')
            .replace(/\s+/g, ' ')
            .trim();
    }

    function editableText(element) {
        if (
            element.childElementCount === 0
        ) {
            return (
                element.textContent || ''
            )
                .replace(/\s+/g, ' ')
                .trim();
        }

        const direct = directText(element);
        if (direct) return direct;

        // Many storefront headings/buttons contain nested spans or icons.
        // Fall back to their rendered text so the visual editor can still
        // expose and edit them instead of treating them as non-text boxes.
        return (
            element.innerText ||
            element.textContent ||
            ''
        )
            .replace(/\s+/g, ' ')
            .trim();
    }

    function firstEditableTextNode(element) {
        const walker = document.createTreeWalker(
            element,
            NodeFilter.SHOW_TEXT,
            {
                acceptNode(node) {
                    if (!node.nodeValue || !node.nodeValue.trim()) {
                        return NodeFilter.FILTER_SKIP;
                    }

                    const parent = node.parentElement;
                    if (
                        parent &&
                        parent.closest(
                            'script,style,noscript,template'
                        )
                    ) {
                        return NodeFilter.FILTER_SKIP;
                    }

                    return NodeFilter.FILTER_ACCEPT;
                }
            }
        );

        return walker.nextNode();
    }

    function replaceEditableText(
        element,
        value
    ) {
        if (
            element.childElementCount === 0
        ) {
            element.textContent = value;
            return;
        }

        const nodes = Array.from(
            element.childNodes
        ).filter(
            (node) =>
                node.nodeType ===
                    Node.TEXT_NODE &&
                node.nodeValue.trim()
        );

        if (nodes.length) {
            nodes[0].nodeValue =
                ` ${value} `;

            nodes
                .slice(1)
                .forEach((node) => {
                    node.nodeValue = '';
                });
            return;
        }

        const nested = firstEditableTextNode(element);
        if (nested) {
            nested.nodeValue = ` ${value} `;
        }
    }

    function backgroundSource(element) {
        const value =
            window.getComputedStyle(
                element
            ).backgroundImage || '';

        const match = value.match(
            /^url\(["']?(.*?)["']?\)$/i
        );

        return match
            ? match[1]
            : '';
    }

    function autoTagElements() {
        const selector = [
            'h1',
            'h2',
            'h3',
            'h4',
            'h5',
            'h6',
            'p',
            'span',
            'a',
            'button',
            'label',
            'small',
            'strong',
            'b',
            'em',
            'li',
            'dt',
            'dd',
            'th',
            'td',
            'figcaption',
            'blockquote',
            'img',
            'section',
            'article',
            '[style*="background-image"]'
        ].join(',');

        document
            .querySelectorAll(selector)
            .forEach((element) => {
                if (
                    element.hasAttribute(
                        'data-bsg-edit'
                    ) ||
                    element.closest(
                        '[data-bsg-edit]'
                    )?.dataset.bsgCreated ===
                        '1' ||
                    element.closest(
                        'script,style,noscript,template,svg'
                    ) ||
                    element.closest(
                        '[data-no-visual-edit]'
                    )
                ) {
                    return;
                }

                const text =
                    editableText(element);

                const hasImage =
                    element.tagName === 'IMG' ||
                    Boolean(
                        backgroundSource(
                            element
                        )
                    );

                const isLayout = [
                    'SECTION',
                    'ARTICLE'
                ].includes(
                    element.tagName
                );

                if (
                    !text &&
                    !hasImage &&
                    !isLayout
                ) {
                    return;
                }

                const id =
                    `auto-${shortHash(
                        stablePath(element)
                    )}`;

                element.dataset.bsgEdit =
                    id;

                const label = (
                    element.getAttribute(
                        'alt'
                    ) ||
                    element.getAttribute(
                        'title'
                    ) ||
                    text
                )
                    .trim()
                    .replace(/\s+/g, ' ')
                    .slice(0, 45);

                element.dataset.bsgName =
                    label ||
                    (
                        hasImage
                            ? 'تصویر صفحه'
                            : 'بخش صفحه'
                    );

                element.dataset.bsgKind =
                    hasImage
                        ? 'image'
                        : (
                            isLayout && !text
                                ? 'box'
                                : 'text'
                        );
            });
    }

    function getBreakpoint() {
        if (window.innerWidth < 640) {
            return 'mobile';
        }

        if (window.innerWidth < 1024) {
            return 'tablet';
        }

        return 'desktop';
    }

    function currentPosition(rule) {
        const responsive =
            rule &&
            rule.responsive &&
            typeof rule.responsive ===
                'object'
                ? rule.responsive
                : {};

        const fallback =
            rule &&
            rule.position &&
            typeof rule.position ===
                'object'
                ? rule.position
                : {};

        return Object.assign(
            {
                x: 0,
                y: 0,
                width: 0,
                height: 0,
                zIndex: 0
            },
            currentBreakpoint ===
                'desktop'
                ? fallback
                : {},
            responsive[
                currentBreakpoint
            ] || {}
        );
    }

    function findRule(id) {
        return (
            rules.find(
                (rule) =>
                    rule &&
                    rule.id === id
            ) || null
        );
    }

    function upsertRule(incoming) {
        if (
            !incoming ||
            !incoming.id
        ) {
            return;
        }

        const index =
            rules.findIndex(
                (rule) =>
                    rule &&
                    rule.id ===
                        incoming.id
            );

        if (index === -1) {
            rules.push(incoming);
        } else {
            rules[index] =
                Object.assign(
                    {},
                    rules[index],
                    incoming
                );
        }
    }

    function capture(element) {
        if (
            snapshots.has(element) ||
            element.dataset.bsgCreated ===
                '1'
        ) {
            return;
        }

        snapshots.set(element, {
            style:
                element.getAttribute(
                    'style'
                ),

            text:
                element.childElementCount ===
                0
                    ? element.textContent
                    : null,

            directTextNodes:
                Array.from(
                    element.childNodes
                )
                    .filter(
                        (node) =>
                            node.nodeType ===
                            Node.TEXT_NODE
                    )
                    .map(
                        (node) => ({
                            node,
                            value:
                                node.nodeValue
                        })
                    ),

            src:
                element.tagName ===
                'IMG'
                    ? element.getAttribute(
                        'src'
                    )
                    : null,

            href:
                element.tagName ===
                'A'
                    ? element.getAttribute(
                        'href'
                    )
                    : null,

            hidden:
                element.hidden
        });
    }

    function restore(element) {
        const snapshot =
            snapshots.get(element);

        if (!snapshot) return;

        if (
            snapshot.style === null
        ) {
            element.removeAttribute(
                'style'
            );
        } else {
            element.setAttribute(
                'style',
                snapshot.style
            );
        }

        if (
            snapshot.text !== null
        ) {
            element.textContent =
                snapshot.text;
        } else {
            snapshot.directTextNodes
                .forEach(
                    ({
                        node,
                        value
                    }) => {
                        if (
                            node.parentNode ===
                            element
                        ) {
                            node.nodeValue =
                                value;
                        }
                    }
                );
        }

        if (
            element.tagName === 'IMG'
        ) {
            if (
                snapshot.src === null
            ) {
                element.removeAttribute(
                    'src'
                );
            } else {
                element.setAttribute(
                    'src',
                    snapshot.src
                );
            }
        }

        if (
            element.tagName === 'A'
        ) {
            if (
                snapshot.href === null
            ) {
                element.removeAttribute(
                    'href'
                );
            } else {
                element.setAttribute(
                    'href',
                    snapshot.href
                );
            }
        }

        element.hidden =
            snapshot.hidden;

        element.classList.remove(
            'bsg-edited',
            'bsg-selected'
        );
    }

    function createElement(rule) {
        const parentId =
            rule.parent ||
            'main-content';

        const parent =
            document.querySelector(
                `[data-bsg-edit="${safeSelector(
                    parentId
                )}"]`
            ) ||
            document.querySelector(
                'main'
            ) ||
            document.body;

        const element =
            document.createElement(
                'div'
            );

        element.dataset.bsgEdit =
            rule.id;

        element.dataset.bsgName =
            rule.name ||
            'المان سفارشی';

        element.dataset.bsgCreated =
            '1';

        element.className =
            'bsg-custom-element';

        element.style.setProperty('position', 'absolute', 'important');
        element.style.setProperty('top', '0', 'important');
        element.style.setProperty('left', '0', 'important');
        element.style.setProperty('right', 'auto', 'important');
        element.style.setProperty('margin', '0', 'important');
        element.style.setProperty('box-sizing', 'border-box', 'important');

        if (
            rule.kind === 'image'
        ) {
            element.style.display =
                'block';

            element.style.width =
                '260px';

            element.style.height =
                '180px';

            element.style.overflow =
                'visible';

            const image =
                document.createElement(
                    'img'
                );

            image.className =
                'bsg-custom-image-node';

            image.alt =
                rule.name ||
                'تصویر سفارشی';

            image.draggable = false;

            image.style.display =
                'block';

            image.style.width =
                '100%';

            image.style.height =
                '100%';

            image.style.objectFit =
                'cover';

            image.style.borderRadius =
                'inherit';

            image.style.pointerEvents =
                'none';

            element.appendChild(
                image
            );

            const resizeHandle =
                document.createElement(
                    'span'
                );

            resizeHandle.className =
                'bsg-resize-handle';

            resizeHandle.dataset.bsgResize =
                'se';

            resizeHandle.setAttribute(
                'aria-hidden',
                'true'
            );

            element.appendChild(
                resizeHandle
            );
        } else {
            element.style.display =
                'block';

            element.style.maxWidth =
                'min(90vw, 640px)';

            element.style.whiteSpace =
                'pre-wrap';

            element.style.minWidth =
                '72px';

            element.style.minHeight =
                '34px';
        }

        if (
            window.getComputedStyle(
                parent
            ).position === 'static'
        ) {
            parent.style.position =
                'relative';
        }

        parent.appendChild(element);

        return element;
    }

    function applyRule(rule) {
        if (
            !rule ||
            !rule.id
        ) {
            return;
        }

        let elements =
            Array.from(
                document.querySelectorAll(
                    `[data-bsg-edit="${safeSelector(
                        rule.id
                    )}"]`
                )
            );

        if (
            !elements.length &&
            rule.created
        ) {
            elements = [
                createElement(rule)
            ];
        }

        elements.forEach(
            (element) => {
                capture(element);

                if (
                    rule.text !==
                        undefined &&
                    rule.kind !==
                        'image' &&
                    (
                        rule.created ||
                        editableText(
                            element
                        )
                    )
                ) {
                    replaceEditableText(
                        element,
                        rule.text
                    );
                }

                if (rule.src) {
                    const customImage =
                        element.querySelector(
                            '.bsg-custom-image-node'
                        );

                    if (customImage) {
                        customImage.src =
                            rule.src;
                    } else if (
                        element.tagName ===
                        'IMG'
                    ) {
                        element.src =
                            rule.src;
                    } else {
                        element.style.setProperty(
                            'background-image',
                            `url("${rule.src.replace(/"/g, '')}")`,
                            'important'
                        );
                        element.style.setProperty(
                            'background-size',
                            'cover',
                            'important'
                        );
                        element.style.setProperty(
                            'background-position',
                            'center',
                            'important'
                        );
                        element.style.setProperty(
                            'background-repeat',
                            'no-repeat',
                            'important'
                        );
                    }
                }

                if (
                    rule.href &&
                    element.tagName ===
                        'A'
                ) {
                    element.href =
                        rule.href;
                }

                STYLE_KEYS.forEach(
                    (key) => {
                        if (
                            rule.styles &&
                            rule.styles[key] !==
                                undefined
                        ) {
                            const cssName = key.replace(
                                /[A-Z]/g,
                                (letter) => '-' + letter.toLowerCase()
                            );

                            // Storefront theme CSS intentionally contains
                            // several !important declarations. Visual edits
                            // must win over those rules or the inspector looks
                            // broken even though a rule was saved correctly.
                            element.style.setProperty(
                                cssName,
                                String(rule.styles[key]),
                                'important'
                            );
                        }
                    }
                );

                if (
                    rule.kind ===
                    'image'
                ) {
                    const customImage =
                        element.querySelector(
                            '.bsg-custom-image-node'
                        );

                    if (customImage) {
                        customImage.style.setProperty(
                            'object-fit',
                            rule.styles?.objectFit || 'cover',
                            'important'
                        );

                        customImage.style.setProperty(
                            'border-radius',
                            'inherit',
                            'important'
                        );
                    }
                }

                const position =
                    currentPosition(
                        rule
                    );

                element.style.setProperty(
                    'translate',
                    `${Number(position.x) || 0}px ${Number(position.y) || 0}px`,
                    'important'
                );

                if (
                    Number(
                        position.width
                    ) > 0
                ) {
                    element.style.setProperty(
                        'width',
                        `${Number(position.width)}px`,
                        'important'
                    );
                } else if (
                    rule.created &&
                    rule.kind !==
                        'image'
                ) {
                    element.style.width =
                        'max-content';
                }

                if (
                    Number(
                        position.height
                    ) > 0
                ) {
                    element.style.setProperty(
                        'height',
                        `${Number(position.height)}px`,
                        'important'
                    );
                } else if (
                    rule.created &&
                    rule.kind !==
                        'image'
                ) {
                    element.style.height =
                        'auto';
                }

                if (
                    Number(
                        position.zIndex
                    )
                ) {
                    if (!rule.created) {
                        element.style.position =
                            'relative';
                    }

                    element.style.setProperty(
                        'z-index',
                        String(Number(position.zIndex)),
                        'important'
                    );
                }

                element.hidden =
                    rule.hidden === true;

                element.classList.add(
                    'bsg-edited'
                );
            }
        );
    }

    function applyTheme() {
        const root =
            document.documentElement;

        const variables = {
            primary: [
                '--primary-color',
                '--site-primary',
                '--lux-gold',
                '--p-gold'
            ],
            secondary: [
                '--secondary-color',
                '--site-secondary',
                '--lux-brown',
                '--p-gold-deep'
            ],
            accent: [
                '--accent-color',
                '--site-accent',
                '--lux-gold-light',
                '--p-gold-pale'
            ],
            bg: [
                '--bg-color',
                '--lux-canvas',
                '--p-bg'
            ],
            text: [
                '--text-color',
                '--lux-text',
                '--p-text'
            ]
        };

        Object.keys(variables).forEach((key) => {
            if (!theme[key]) return;

            variables[key].forEach((name) => {
                root.style.setProperty(
                    name,
                    theme[key],
                    'important'
                );
            });
        });
    }

    function applyAll() {
        // Re-scan on every full apply so content injected after initial page
        // load (slider content, dynamic cards, etc.) also becomes editable.
        autoTagElements();

        document
            .querySelectorAll(
                '[data-bsg-created="1"]'
            )
            .forEach(
                (element) =>
                    element.remove()
            );

        snapshots.forEach(
            (
                snapshot,
                element
            ) => restore(element)
        );

        rules.forEach(
            applyRule
        );

        applyTheme();
    }

    function describe(element) {
        const id =
            element.dataset.bsgEdit;

        const computed =
            window.getComputedStyle(
                element
            );

        const saved =
            findRule(id) || {};

        const text =
            editableText(element);

        const customImage =
            element.querySelector?.(
                '.bsg-custom-image-node'
            );

        const imageSource =
            customImage
                ? (
                    customImage.currentSrc ||
                    customImage.src
                )
                : (
                    element.tagName ===
                    'IMG'
                        ? (
                            element.currentSrc ||
                            element.src
                        )
                        : backgroundSource(
                            element
                        )
                );

        return {
            id,

            name:
                element.dataset.bsgName ||
                saved.name ||
                id,

            kind:
                customImage ||
                element.tagName ===
                    'IMG'
                    ? 'image'
                    : (
                        saved.kind ||
                        element.dataset.bsgKind ||
                        (
                            text
                                ? 'text'
                                : 'box'
                        )
                    ),

            tag:
                element.tagName.toLowerCase(),

            text:
                saved.text !== undefined
                    ? saved.text
                    : text,

            src:
                saved.src ||
                imageSource ||
                '',

            href:
                saved.href ||
                (
                    element.tagName ===
                    'A'
                        ? (
                            element.getAttribute(
                                'href'
                            ) || ''
                        )
                        : ''
                ),

            hidden:
                saved.hidden === true,

            created:
                saved.created === true,

            parent:
                saved.parent ||
                'main-content',

            styles:
                Object.assign(
                    {
                        color:
                            computed.color,

                        backgroundColor:
                            computed.backgroundColor,

                        fontSize:
                            computed.fontSize,

                        fontWeight:
                            computed.fontWeight,

                        textAlign:
                            computed.textAlign,

                        borderRadius:
                            computed.borderRadius,

                        opacity:
                            computed.opacity,

                        objectFit:
                            computed.objectFit
                    },

                    saved.styles ||
                    {}
                ),

            responsive:
                saved.responsive ||
                {},

            position:
                currentPosition(
                    saved
                )
        };
    }

    function post(message) {
        if (editMode) {
            window.parent.postMessage(
                message,
                window.location.origin
            );
        }
    }

    function select(element) {
        if (selectedElement) {
            selectedElement
                .classList
                .remove(
                    'bsg-selected'
                );
        }

        selectedElement =
            element;

        if (!element) return;

        element.classList.add(
            'bsg-selected'
        );

        post({
            type:
                'bsg-element-selected',

            element:
                describe(element)
        });
    }

    function editorClick(event) {
        if (editorMode === 'off') return;

        const target =
            event.target.closest(
                '[data-bsg-edit]'
            );

        if (!target) return;

        // While editing, storefront links/buttons must never navigate away
        // from the iframe.  In Move mode a completed drag is followed by a
        // synthetic click in Chromium; suppress it as well.
        event.preventDefault();
        event.stopPropagation();

        if (Date.now() < suppressClickUntil) {
            return;
        }

        if (editorMode === 'select') {
            select(target);
        }
    }

    function pointerDown(event) {
        if (
            event.button !== 0 ||
            editorMode === 'off'
        ) {
            return;
        }

        const resizeHandle =
            event.target.closest(
                '[data-bsg-resize]'
            );

        if (resizeHandle) {
            const target =
                resizeHandle.closest(
                    '[data-bsg-edit]'
                );

            if (!target) return;

            event.preventDefault();
            event.stopPropagation();

            select(target);

            const rule =
                findRule(
                    target.dataset
                        .bsgEdit
                );

            if (!rule) return;

            const position =
                currentPosition(
                    rule
                );

            const rect =
                target.getBoundingClientRect();

            resizeState = {
                target,
                rule,

                startX:
                    event.clientX,

                startY:
                    event.clientY,

                baseWidth:
                    Number(
                        position.width
                    ) ||
                    rect.width,

                baseHeight:
                    Number(
                        position.height
                    ) ||
                    rect.height
            };

            resizeHandle
                .setPointerCapture?.(
                    event.pointerId
                );

            target.classList.add(
                'bsg-resizing'
            );

            return;
        }

        // Dragging is intentionally available in both Select and Move.
        // In Select a normal click still selects the element, while a real
        // pointer movement turns into a drag. This matches the older visual
        // editor workflow and prevents the common "nothing moves" feeling.
        if (!['select', 'move'].includes(editorMode)) {
            return;
        }

        const target =
            event.target.closest(
                '[data-bsg-edit]'
            );

        if (!target) return;

        if (
            event.target.closest(
                'input,textarea,select,option,[contenteditable="true"]'
            )
        ) {
            return;
        }

        select(target);

        const rule =
            findRule(
                target.dataset
                    .bsgEdit
            ) || {
                id:
                    target.dataset
                        .bsgEdit,

                name:
                    target.dataset
                        .bsgName ||
                    target.dataset
                        .bsgEdit,

                kind:
                    target.tagName ===
                    'IMG'
                        ? 'image'
                        : (
                            editableText(
                                target
                            )
                                ? 'text'
                                : 'box'
                        ),

                text:
                    target.tagName ===
                    'IMG'
                        ? ''
                        : editableText(
                            target
                        ),

                src:
                    target.tagName ===
                    'IMG'
                        ? target.src
                        : backgroundSource(
                            target
                        ),

                styles: {},
                responsive: {},
                hidden: false
            };

        const position =
            currentPosition(rule);

        dragState = {
            target,
            rule,

            startX:
                event.clientX,

            startY:
                event.clientY,

            baseX:
                Number(
                    position.x
                ) || 0,

            baseY:
                Number(
                    position.y
                ) || 0,

            moved:
                false
        };

        target
            .setPointerCapture?.(
                event.pointerId
            );
    }

    function pointerMove(event) {
        if (resizeState) {
            event.preventDefault();

            const width =
                Math.max(
                    48,
                    Math.round(
                        resizeState
                            .baseWidth +
                        event.clientX -
                        resizeState
                            .startX
                    )
                );

            const height =
                Math.max(
                    48,
                    Math.round(
                        resizeState
                            .baseHeight +
                        event.clientY -
                        resizeState
                            .startY
                    )
                );

            const responsive =
                Object.assign(
                    {},
                    resizeState
                        .rule
                        .responsive ||
                    {}
                );

            responsive[
                currentBreakpoint
            ] = Object.assign(
                {},
                responsive[
                    currentBreakpoint
                ] || {},
                {
                    width,
                    height
                }
            );

            resizeState.rule =
                Object.assign(
                    {},
                    resizeState.rule,
                    {
                        responsive
                    }
                );

            resizeState.target.style.setProperty(
                'width',
                `${width}px`,
                'important'
            );

            resizeState.target.style.setProperty(
                'height',
                `${height}px`,
                'important'
            );

            return;
        }

        if (!dragState) return;

        const dx =
            event.clientX -
            dragState.startX;

        const dy =
            event.clientY -
            dragState.startY;

        if (
            !dragState.moved &&
            Math.hypot(
                dx,
                dy
            ) < 5
        ) {
            return;
        }

        dragState.moved = true;

        event.preventDefault();

        const responsive =
            Object.assign(
                {},
                dragState
                    .rule
                    .responsive ||
                {}
            );

        responsive[
            currentBreakpoint
        ] = Object.assign(
            {},
            responsive[
                currentBreakpoint
            ] || {},
            {
                x:
                    Math.round(
                        dragState
                            .baseX +
                        dx
                    ),

                y:
                    Math.round(
                        dragState
                            .baseY +
                        dy
                    )
            }
        );

        dragState.rule =
            Object.assign(
                {},
                dragState.rule,
                {
                    responsive
                }
            );

        const position =
            responsive[
                currentBreakpoint
            ];

        dragState.target.style.setProperty(
            'translate',
            `${position.x}px ${position.y}px`,
            'important'
        );

        dragState
            .target
            .classList
            .add(
                'bsg-dragging'
            );
    }

    function pointerUp() {
        if (resizeState) {
            resizeState
                .target
                .classList
                .remove(
                    'bsg-resizing'
                );

            upsertRule(
                resizeState.rule
            );

            post({
                type:
                    'bsg-rule-changed',

                rule:
                    resizeState.rule
            });

            select(
                resizeState.target
            );

            resizeState = null;

            return;
        }

        if (!dragState) return;

        dragState
            .target
            .classList
            .remove(
                'bsg-dragging'
            );

        if (dragState.moved) {
            upsertRule(
                dragState.rule
            );

            post({
                type:
                    'bsg-rule-changed',

                rule:
                    dragState.rule
            });

            select(
                dragState.target
            );

            suppressClickUntil =
                Date.now() + 350;
        }

        dragState = null;
    }

    function applyEditorMode(mode) {
        editorMode =
            ['off', 'select', 'move'].includes(mode)
                ? mode
                : 'select';

        document.documentElement.classList.toggle(
            'bsg-edit-mode',
            editorMode !== 'off'
        );
        document.documentElement.classList.toggle(
            'bsg-move-mode',
            editorMode === 'move'
        );
        document.documentElement.classList.toggle(
            'bsg-select-mode',
            editorMode === 'select'
        );

        if (editorMode === 'off' && selectedElement) {
            selectedElement.classList.remove('bsg-selected');
            selectedElement = null;
        }
    }

    function enableEditor() {
        applyEditorMode(editorMode);

        document.addEventListener(
            'click',
            editorClick,
            true
        );

        document.addEventListener(
            'pointerdown',
            pointerDown,
            true
        );

        document.addEventListener(
            'pointermove',
            pointerMove,
            true
        );

        document.addEventListener(
            'pointerup',
            pointerUp,
            true
        );

        document.addEventListener(
            'pointercancel',
            pointerUp,
            true
        );

        document.addEventListener(
            'dragstart',
            (event) =>
                event.preventDefault(),
            true
        );

        post({
            type:
                'bsg-ready',

            path:
                window.location.pathname
        });
    }

    // Same-origin direct bridge used by the studio as a reliable
    // fallback to postMessage. The iframe is sandboxed with allow-same-origin,
    // so the parent can call these methods safely when both pages belong to
    // this storefront.
    window.BSGCustomizer = {
        status() {
            return {
                canEdit,
                editRequested,
                editMode,
                editorMode,
                breakpoint: currentBreakpoint,
                ready: true
            };
        },
        setEditorMode(mode) {
            applyEditorMode(mode);
        },
        setRules(nextRules) {
            rules = Array.isArray(nextRules) ? nextRules : [];
            applyAll();
        },
        setTheme(nextTheme) {
            theme = nextTheme && typeof nextTheme === 'object'
                ? nextTheme
                : {};
            applyTheme();
        },
        setBreakpoint(nextBreakpoint) {
            currentBreakpoint = [
                'desktop',
                'tablet',
                'mobile'
            ].includes(nextBreakpoint)
                ? nextBreakpoint
                : getBreakpoint();
            applyAll();
        },
        applyRule(rule) {
            if (!rule) return;
            upsertRule(rule);
            applyAll();
            const element = document.querySelector(
                `[data-bsg-edit="${safeSelector(rule.id)}"]`
            );
            if (element) select(element);
        },
        removeRule(id) {
            rules = rules.filter(
                (rule) => rule && rule.id !== id
            );
            selectedElement = null;
            applyAll();
        },
        createRule(rule) {
            if (!rule) return;
            upsertRule(rule);
            applyAll();
            const element = document.querySelector(
                `[data-bsg-edit="${safeSelector(rule.id)}"]`
            );
            if (element) {
                element.scrollIntoView({
                    behavior: 'smooth',
                    block: 'center',
                    inline: 'center'
                });
                select(element);
                post({type: 'bsg-layers-changed'});
            }
        },
        selectId(id) {
            const element = document.querySelector(
                `[data-bsg-edit="${safeSelector(id)}"]`
            );
            if (element) {
                element.scrollIntoView({
                    behavior: 'smooth',
                    block: 'center',
                    inline: 'center'
                });
                select(element);
            }
        },
        requestLayers() {
            const layerList = Array.from(
                document.querySelectorAll('[data-bsg-edit]')
            ).map((element) => ({
                id: element.dataset.bsgEdit,
                name:
                    element.dataset.bsgName ||
                    element.dataset.bsgEdit,
                tag: element.tagName.toLowerCase()
            }));
            post({type: 'bsg-layers', layers: layerList});
            return layerList;
        },
        refresh() {
            autoTagElements();
            applyAll();
        }
    };

    window.addEventListener(
        'message',
        (event) => {
            if (
                !editMode ||
                event.origin !==
                    window.location.origin ||
                event.source !==
                    window.parent
            ) {
                return;
            }

            const data =
                event.data || {};

            if (
                data.type ===
                'bsg-set-editor-mode'
            ) {
                applyEditorMode(data.mode);
            }

            else if (
                data.type ===
                'bsg-set-rules'
            ) {
                rules =
                    Array.isArray(
                        data.rules
                    )
                        ? data.rules
                        : [];

                applyAll();
            }

            else if (
                data.type ===
                'bsg-set-theme'
            ) {
                theme =
                    data.theme &&
                    typeof data.theme ===
                        'object'
                        ? data.theme
                        : {};

                applyTheme();
            }

            else if (
                data.type ===
                'bsg-set-breakpoint'
            ) {
                currentBreakpoint =
                    [
                        'desktop',
                        'tablet',
                        'mobile'
                    ].includes(
                        data.breakpoint
                    )
                        ? data.breakpoint
                        : getBreakpoint();

                applyAll();
            }

            else if (
                data.type ===
                    'bsg-apply-rule' &&
                data.rule
            ) {
                upsertRule(
                    data.rule
                );

                applyAll();

                const element =
                    document.querySelector(
                        `[data-bsg-edit="${safeSelector(
                            data.rule.id
                        )}"]`
                    );

                if (element) {
                    select(element);
                }
            }

            else if (
                data.type ===
                    'bsg-remove-rule' &&
                data.id
            ) {
                rules =
                    rules.filter(
                        (rule) =>
                            rule &&
                            rule.id !==
                                data.id
                    );

                selectedElement =
                    null;

                applyAll();
            }

            else if (
                data.type ===
                    'bsg-create-rule' &&
                data.rule
            ) {
                upsertRule(
                    data.rule
                );

                applyAll();

                const element =
                    document.querySelector(
                        `[data-bsg-edit="${safeSelector(
                            data.rule.id
                        )}"]`
                    );

                if (element) {
                    element.scrollIntoView({
                        behavior:
                            'smooth',

                        block:
                            'center',

                        inline:
                            'center'
                    });

                    select(element);

                    post({
                        type:
                            'bsg-layers-changed'
                    });
                }
            }

            else if (
                data.type ===
                    'bsg-select-id' &&
                data.id
            ) {
                const element =
                    document.querySelector(
                        `[data-bsg-edit="${safeSelector(
                            data.id
                        )}"]`
                    );

                if (element) {
                    element.scrollIntoView({
                        behavior:
                            'smooth',

                        block:
                            'center'
                    });

                    select(element);
                }
            }

            else if (
                data.type ===
                'bsg-request-layers'
            ) {
                const layers =
                    Array.from(
                        document.querySelectorAll(
                            '[data-bsg-edit]'
                        )
                    ).map(
                        (element) => ({
                            id:
                                element.dataset
                                    .bsgEdit,

                            name:
                                element.dataset
                                    .bsgName ||
                                element.dataset
                                    .bsgEdit,

                            tag:
                                element.tagName
                                    .toLowerCase()
                        })
                    );

                post({
                    type:
                        'bsg-layers',

                    layers
                });
            }
        }
    );

    const editorStyle =
        document.createElement(
            'style'
        );

    editorStyle.textContent = `
        .bsg-custom-element {
            box-sizing: border-box;
            touch-action: none;
            user-select: none;
        }

        .bsg-custom-image-node {
            display: block;
            width: 100%;
            height: 100%;
            pointer-events: none;
        }

        .bsg-resize-handle {
            position: absolute;
            right: -9px;
            bottom: -9px;
            z-index: 10000;
            display: none;
            width: 20px;
            height: 20px;
            border: 3px solid #fff;
            border-radius: 7px;
            background:
                linear-gradient(
                    135deg,
                    #c9954d,
                    #7a4a2b
                );
            box-shadow:
                0 5px 16px
                rgba(122, 74, 43, .42);
            cursor: nwse-resize !important;
            pointer-events: auto;
            touch-action: none;
        }

        .bsg-edit-mode
        [data-bsg-edit].bsg-selected
        > .bsg-resize-handle {
            display: block;
        }

        .bsg-edit-mode
        [data-bsg-edit] {
            cursor: pointer !important;
        }

        .bsg-move-mode
        [data-bsg-edit] {
            cursor: grab !important;
        }

        .bsg-move-mode
        [data-bsg-edit]:active {
            cursor: grabbing !important;
        }

        .bsg-edit-mode
        [data-bsg-edit]:hover {
            outline:
                2px dashed
                #c9954d !important;
            outline-offset: 3px;
        }

        .bsg-edit-mode
        [data-bsg-edit].bsg-selected {
            outline:
                3px solid
                #7a4a2b !important;
            outline-offset: 4px;
            box-shadow:
                0 0 0 6px
                rgba(
                    124,
                    58,
                    237,
                    .13
                ) !important;
        }

        .bsg-edit-mode
        [data-bsg-created="1"]
        .bsg-selected::after,
        .bsg-edit-mode
        [data-bsg-created="1"].bsg-selected::after {
            content:
                'المان جدید • بکش و جابه‌جا کن';
            position: absolute;
            inset:
                auto 0
                calc(100% + 9px)
                auto;
            width: max-content;
            max-width: 220px;
            padding: 6px 9px;
            border-radius: 8px;
            color: #fff;
            background: #7a4a2b;
            box-shadow:
                0 8px 25px
                rgba(
                    15,
                    23,
                    42,
                    .3
                );
            font:
                700 11px/1.5
                Vazir,
                Tahoma,
                sans-serif;
            pointer-events: none;
        }

        .bsg-edit-mode
        [data-bsg-edit].bsg-dragging {
            cursor:
                grabbing !important;
            opacity: .88;
        }

        .bsg-edit-mode
        [data-bsg-edit].bsg-resizing {
            outline-color:
                #c9954d !important;
        }

        .bsg-edit-mode a,
        .bsg-edit-mode button {
            pointer-events: auto;
        }
    `;

    document.head.appendChild(
        editorStyle
    );

    autoTagElements();
    applyAll();

    if (editMode) {
        enableEditor();
    }

    let resizeTimer = null;

    window.addEventListener(
        'resize',
        () => {
            window.clearTimeout(
                resizeTimer
            );

            resizeTimer =
                window.setTimeout(
                    () => {
                        if (!editMode) {
                            currentBreakpoint =
                                getBreakpoint();
                        }

                        applyAll();
                    },
                    120
                );
        }
    );
})();