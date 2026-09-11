// ===== متغیرهای انتخاب رنگ و تعداد =====
let selectedColorId = null;
let selectedColorName = '';
let selectedColorCode = '';
let selectedStock = 0;
let selectedPrice = 0;
let currentQuantity = 1;

// ===== گالری و زوم =====
let currentImageIndex = 0;
let images = [];

// ===== انتخاب رنگ =====
function selectColor(element, colorId, colorCode, stock, price) {
    document.querySelectorAll('.color-option').forEach(btn => {
        btn.classList.remove('border-pink-500', 'ring-2', 'ring-pink-200');
        btn.classList.add('border-gray-300');
    });
    
    element.classList.add('border-pink-500', 'ring-2', 'ring-pink-200');
    element.classList.remove('border-gray-300');
    
    selectedColorId = colorId;
    selectedColorName = element.dataset.colorName;
    selectedColorCode = colorCode;
    selectedStock = stock;
    selectedPrice = price;
    
    document.getElementById('productPrice').textContent = price.toLocaleString();
    document.getElementById('selectedColorName').innerHTML = 
        `رنگ انتخاب شده: <span class="font-bold text-gray-700">${selectedColorName}</span>`;
    
    document.getElementById('stockCount').textContent = stock;
    
    const warning = document.getElementById('lowStockWarning');
    if (stock <= 5 && stock > 0) {
        warning.classList.remove('hidden');
        document.getElementById('lowStockCount').textContent = stock;
    } else {
        warning.classList.add('hidden');
    }
    
    document.getElementById('quantityInput').max = stock;
    if (currentQuantity > stock) {
        currentQuantity = stock;
        document.getElementById('quantityInput').value = stock;
    }
}

// ===== تغییر تعداد =====
function changeQuantity(delta) {
    const input = document.getElementById('quantityInput');
    let value = parseInt(input.value) + delta;
    const max = parseInt(input.max) || selectedStock || 10;
    
    if (value < 1) value = 1;
    if (value > max) value = max;
    
    input.value = value;
    currentQuantity = value;
}

// ===== اضافه کردن به سبد با رنگ =====
function addToCartWithColor() {
    if (!selectedColorId) {
        alert('لطفاً یک رنگ را انتخاب کنید');
        return;
    }
    const quantity = parseInt(document.getElementById('quantityInput').value);
    if (quantity > selectedStock) {
        alert(`موجودی کافی نیست. فقط ${selectedStock} عدد موجود است.`);
        return;
    }
    const productId = document.getElementById('productId').value;
    window.location.href = `/cart/add/${productId}/?color=${selectedColorId}&qty=${quantity}`;
}

// ===== خرید سریع با رنگ =====
function quickBuyWithColor() {
    if (!selectedColorId) {
        alert('لطفاً یک رنگ را انتخاب کنید');
        return;
    }
    const quantity = parseInt(document.getElementById('quantityInput').value);
    if (quantity > selectedStock) {
        alert(`موجودی کافی نیست. فقط ${selectedStock} عدد موجود است.`);
        return;
    }
    const productId = document.getElementById('productId').value;
    window.location.href = `/cart/add/${productId}/?color=${selectedColorId}&qty=${quantity}&next=/checkout/`;
}

// ===== گالری =====
function changeImage(src, index, element) {
    document.getElementById('mainImage').src = src;
    currentImageIndex = index;
    document.querySelectorAll('.product-gallery-thumb').forEach(el => {
        el.classList.remove('active', 'border-pink-500');
        el.classList.add('border-transparent');
    });
    element.classList.add('active', 'border-pink-500');
    element.classList.remove('border-transparent');
}

function openGallery(index) {
    currentImageIndex = index;
    document.getElementById('modalImage').src = images[index];
    document.getElementById('galleryModal').classList.add('active');
    document.body.style.overflow = 'hidden';
}

function closeGallery(event) {
    if (event.target === event.currentTarget || event.target.className === 'close-modal') {
        document.getElementById('galleryModal').classList.remove('active');
        document.body.style.overflow = 'auto';
    }
}

function changeGalleryImage(direction, event) {
    event.stopPropagation();
    currentImageIndex = (currentImageIndex + direction + images.length) % images.length;
    document.getElementById('modalImage').src = images[currentImageIndex];
}

// ===== انتخاب رنگ با کلیک روی تصویر =====
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.product-gallery-thumb, .zoom-container img').forEach(el => {
        el.addEventListener('click', function() {
            const alt = this.alt || '';
            document.querySelectorAll('.color-option').forEach(btn => {
                if (btn.dataset.colorName === alt || btn.dataset.colorName === alt.split(' ')[0]) {
                    btn.click();
                }
            });
        });
    });
    
    // مقداردهی اولیه
    const firstColor = document.querySelector('.color-option');
    if (firstColor) {
        firstColor.click();
    }
    
    const input = document.getElementById('quantityInput');
    input.max = selectedStock || parseInt(document.getElementById('totalStock').value) || 10;
    
    if (selectedStock <= 5 && selectedStock > 0) {
        document.getElementById('lowStockWarning').classList.remove('hidden');
        document.getElementById('lowStockCount').textContent = selectedStock;
    }
});

// ===== نظرات =====
function showReviewForm() {
    document.getElementById('reviewForm').classList.remove('hidden');
}
function hideReviewForm() {
    document.getElementById('reviewForm').classList.add('hidden');
}

document.querySelectorAll('.rating-select').forEach(star => {
    star.addEventListener('click', function() {
        const value = parseInt(this.dataset.value);
        document.getElementById('selectedRating').value = value;
        document.querySelectorAll('.rating-select').forEach((s, index) => {
            if (index < value) {
                s.textContent = '★';
                s.style.color = '#fbbf24';
            } else {
                s.textContent = '☆';
                s.style.color = '#d1d5db';
            }
        });
    });
});

// ===== اشتراک‌گذاری =====
function shareProduct() {
    if (navigator.share) {
        navigator.share({
            title: document.title,
            text: document.querySelector('.short-description')?.textContent || '',
            url: window.location.href
        });
    } else {
        navigator.clipboard.writeText(window.location.href).then(() => {
            alert('✅ لینک محصول کپی شد!');
        });
    }
}

// ===== کیبورد برای گالری =====
document.addEventListener('keydown', function(e) {
    const modal = document.getElementById('galleryModal');
    if (modal && modal.classList.contains('active')) {
        if (e.key === 'ArrowLeft') {
            currentImageIndex = (currentImageIndex - 1 + images.length) % images.length;
            document.getElementById('modalImage').src = images[currentImageIndex];
        } else if (e.key === 'ArrowRight') {
            currentImageIndex = (currentImageIndex + 1) % images.length;
            document.getElementById('modalImage').src = images[currentImageIndex];
        } else if (e.key === 'Escape') {
            modal.classList.remove('active');
            document.body.style.overflow = 'auto';
        }
    }
});