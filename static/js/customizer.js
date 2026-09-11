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

        return directText(element);
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

        if (!nodes.length) return;

        nodes[0].nodeValue =
            ` ${value} `;

        nodes
            .slice(1)
            .forEach((node) => {
                node.nodeValue = '';
            });
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

        element.style.position =
            'absolute';

        element.style.top = '0';
        element.style.left = '0';
        element.style.right = 'auto';
        element.style.margin = '0';

        element.style.boxSizing =
            'border-box';

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
                        element.style.backgroundImage =
                            `url("${rule.src.replace(
                                /"/g,
                                ''
                            )}")`;

                        element.style.backgroundSize =
                            'cover';

                        element.style.backgroundPosition =
                            'center';

                        element.style.backgroundRepeat =
                            'no-repeat';
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
                            element.style[key] =
                                rule.styles[
                                    key
                                ];
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
                        customImage.style.objectFit =
                            rule.styles
                                ?.objectFit ||
                            'cover';

                        customImage.style.borderRadius =
                            'inherit';
                    }
                }

                const position =
                    currentPosition(
                        rule
                    );

                element.style.translate =
                    `${Number(
                        position.x
                    ) || 0}px ` +
                    `${Number(
                        position.y
                    ) || 0}px`;

                if (
                    Number(
                        position.width
                    ) > 0
                ) {
                    element.style.width =
                        `${Number(
                            position.width
                        )}px`;
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
                    element.style.height =
                        `${Number(
                            position.height
                        )}px`;
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

                    element.style.zIndex =
                        String(
                            Number(
                                position.zIndex
                            )
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
            primary:
                '--primary-color',

            secondary:
                '--secondary-color',

            accent:
                '--accent-color',

            bg:
                '--bg-color',

            text:
                '--text-color'
        };

        Object.keys(
            variables
        ).forEach((key) => {
            if (theme[key]) {
                root.style.setProperty(
                    variables[key],
                    theme[key]
                );
            }
        });
    }

    function applyAll() {
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
        const target =
            event.target.closest(
                '[data-bsg-edit]'
            );

        if (!target) return;

        event.preventDefault();
        event.stopPropagation();

        select(target);
    }

    function pointerDown(event) {
        if (
            event.button !== 0
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

        const target =
            event.target.closest(
                '[data-bsg-edit]'
            );

        if (!target) return;

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

            resizeState
                .target
                .style
                .width =
                    `${width}px`;

            resizeState
                .target
                .style
                .height =
                    `${height}px`;

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

        dragState
            .target
            .style
            .translate =
                `${position.x}px ` +
                `${position.y}px`;

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
        }

        dragState = null;
    }

    function enableEditor() {
        document
            .documentElement
            .classList
            .add(
                'bsg-edit-mode'
            );

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
                    #ec407a,
                    #7c3aed
                );
            box-shadow:
                0 5px 16px
                rgba(124, 58, 237, .42);
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

        .bsg-edit-mode
        [data-bsg-edit]:hover {
            outline:
                2px dashed
                #ec407a !important;
            outline-offset: 3px;
        }

        .bsg-edit-mode
        [data-bsg-edit].bsg-selected {
            outline:
                3px solid
                #7c3aed !important;
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
            background: #7c3aed;
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
                #ec407a !important;
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