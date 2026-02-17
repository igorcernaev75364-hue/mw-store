document.addEventListener("DOMContentLoaded", () => {
    const notice = document.getElementById("notice");
    const floatingCart = document.getElementById("floating-cart");
    let cartData = { cart: [], total: 0 };

    window.toggleCart = function() {
        const cartPreview = document.querySelector(".cart-preview");
        cartPreview.classList.toggle("expanded");
    };

    // Оптимизированная функция добавления в корзину
    document.querySelectorAll(".btn-add").forEach(btn => {
        btn.addEventListener("click", function (e) {
            e.preventDefault();
            const id = this.dataset.id;
            const button = this;

            button.classList.add('btn-loading');
            const originalText = button.innerHTML;
            button.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';

            fetch(`/add_to_cart/${id}`, {
                method: "POST",
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'Content-Type': 'application/json'
                }
            })
                .then(res => {
                    if (!res.ok) throw new Error('Network error');
                    return res.json();
                })
                .then(data => {
                    if (data.status === "ok") {
                        showNotice("✅ Товар добавлен", "success");
                        updateCartCount(data.cart);
                        animateCart();
                    }
                })
                .catch(err => {
                    console.error("Ошибка:", err);
                    showNotice("❌ Ошибка при добавлении", "error");
                })
                .finally(() => {
                    button.classList.remove('btn-loading');
                    button.innerHTML = originalText;
                });
        });
    });

    window.updateQuantity = function(productId, change) {
        fetch(`/update_cart/${productId}`, {
            method: "POST",
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify({ change: change })
        })
            .then(res => res.json())
            .then(data => {
                if (data.status === "ok") {
                    updateCartData();
                    showNotice(change > 0 ? "➕ Количество увеличено" : "➖ Количество уменьшено", "success");
                }
            })
            .catch(err => console.error("Ошибка при обновлении:", err));
    };

    window.removeFromCart = function(productId) {
        fetch(`/remove_from_cart/${productId}`, {
            method: "POST",
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
            .then(res => res.json())
            .then(data => {
                if (data.status === "ok") {
                    updateCartData();
                    showNotice("🗑 Товар удален", "success");
                    animateCart();
                }
            })
            .catch(err => console.error("Ошибка при удалении:", err));
    };

    function updateCartData() {
        fetch("/api/cart")
            .then(res => res.json())
            .then(data => {
                cartData = data;
                updateCartUI();
                updateCartPageUI();
            })
            .catch(err => console.error("Ошибка при получении корзины:", err));
    }

    function updateCartCount(cartData) {
        const cartCount = document.querySelector(".cart-count");
        if (cartCount) {
            const totalItems = Object.values(cartData).reduce((sum, qty) => sum + qty, 0);
            cartCount.textContent = totalItems;
        }
    }

    function updateCartUI() {
        const cartCount = document.querySelector(".cart-count");
        const totalItems = cartData.cart.reduce((sum, item) => sum + item.qty, 0);
        cartCount.textContent = totalItems;

        const cartTotal = document.querySelector(".cart-total");
        cartTotal.textContent = `${cartData.total}₽`;

        const cartItemsContainer = document.querySelector(".cart-items");

        if (cartData.cart.length === 0) {
            cartItemsContainer.innerHTML = `
                <div style="text-align: center; padding: 25px; color: var(--text-secondary);">
                    <i class="fas fa-shopping-bag" style="font-size: 40px; margin-bottom: 15px; opacity: 0.5;"></i>
                    <p style="font-size: 0.95rem;">Корзина пуста</p>
                </div>
            `;
        } else {
            let itemsHtml = "";
            cartData.cart.forEach(item => {
                itemsHtml += `
                    <div class="cart-item" data-product-id="${item.id}">
                        <div class="cart-item-img">
                            ${getProductIcon(item.id)}
                        </div>
                        <div class="cart-item-info">
                            <div class="cart-item-title">${item.title}</div>
                            <div class="cart-item-price">${item.price}₽ × ${item.qty}</div>
                        </div>
                        <div class="cart-item-controls">
                            <div class="qty-control">
                                <button class="qty-btn minus" onclick="updateQuantity(${item.id}, -1)">
                                    <i class="fas fa-minus"></i>
                                </button>
                                <span class="qty-value">${item.qty}</span>
                                <button class="qty-btn plus" onclick="updateQuantity(${item.id}, 1)">
                                    <i class="fas fa-plus"></i>
                                </button>
                            </div>
                            <button class="remove-item" onclick="removeFromCart(${item.id})">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    </div>
                `;
            });
            cartItemsContainer.innerHTML = itemsHtml;
        }
    }

    function updateCartPageUI() {
        const cartPageContainer = document.querySelector(".cart-items-list");
        if (!cartPageContainer) return;

        if (cartData.cart.length === 0) {
            location.reload();
        } else {
            cartData.cart.forEach(item => {
                const itemElement = document.querySelector(`.cart-item-card[data-product-id="${item.id}"]`);
                if (itemElement) {
                    const qtySpan = itemElement.querySelector('.cart-page-qty');
                    const subtotalSpan = itemElement.querySelector('.cart-item-subtotal');
                    if (qtySpan) qtySpan.textContent = item.qty;
                    if (subtotalSpan) subtotalSpan.textContent = `${item.subtotal}₽`;
                }
            });

            const totalElement = document.querySelector('.cart-total-section span:last-child');
            if (totalElement) {
                totalElement.textContent = `${cartData.total}₽`;
            }
        }
    }

    function getProductIcon(id) {
        const icons = {
            1: '<i class="fas fa-tshirt"></i>',
            2: '<i class="fas fa-mug-hot"></i>',
            3: '<i class="fas fa-hoodie"></i>'
        };
        return icons[id] || '<i class="fas fa-tag"></i>';
    }

    function animateCart() {
        const cartPreview = document.querySelector(".cart-preview");
        cartPreview.style.transform = "scale(1.02)";
        setTimeout(() => {
            cartPreview.style.transform = "scale(1)";
        }, 200);
    }

    function showNotice(message, type = "success") {
        if (!notice) return;

        const icon = type === "success" ? "✅" : "❌";
        notice.innerHTML = `${icon} ${message}`;
        notice.classList.add("show");

        setTimeout(() => {
            notice.classList.remove("show");
        }, 1500);
    }

    document.addEventListener("click", (e) => {
        const cartPreview = document.querySelector(".cart-preview");
        if (!floatingCart.contains(e.target) && cartPreview.classList.contains("expanded")) {
            cartPreview.classList.remove("expanded");
        }
    });

    updateCartData();
    setInterval(updateCartData, 5000);
});