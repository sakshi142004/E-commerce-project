// ============================================================
// script.js — BeltPurse Complete Fixed Version
// ============================================================

// ================= POPUP =================
document.addEventListener("DOMContentLoaded", function () {

    const popup     = document.getElementById("popup");
    const blurBg    = document.getElementById("blurBg");
    const loginBtn  = document.getElementById("loginBtn");
    const switchBtn = document.getElementById("switchMode");
    const nameField = document.getElementById("name");
    const titleEl   = document.getElementById("formTitle");
    const mainBtn   = document.getElementById("mainBtn");
    const msg       = document.getElementById("formMsg");
    const togglePwd = document.getElementById("togglePassword");

    let isLogin = true;

    window.openPopup = function () {
        if (!popup) return;
        popup.classList.add("show");
        if (blurBg) blurBg.style.display = "block";
        document.body.style.overflow = "hidden";
    };

    window.closePopup = function () {
        if (!popup) return;
        popup.classList.remove("show");
        if (blurBg) blurBg.style.display = "none";
        document.body.style.overflow = "";
    };

    if (loginBtn) loginBtn.addEventListener("click", e => { e.preventDefault(); openPopup(); });

    const closeBtn = document.getElementById("closeBtn");
    if (closeBtn) closeBtn.onclick = closePopup;

    if (switchBtn) {
        switchBtn.onclick = () => {
            isLogin = !isLogin;
            if (msg) msg.innerText = "";
            if (isLogin) {
                if (titleEl)   titleEl.innerText           = "Login";
                if (nameField) nameField.style.display     = "none";
                if (mainBtn)   mainBtn.innerText           = "Login";
                switchBtn.innerText = "Create Account";
            } else {
                if (titleEl)   titleEl.innerText           = "Register";
                if (nameField) nameField.style.display     = "block";
                if (mainBtn)   mainBtn.innerText           = "Register";
                switchBtn.innerText = "Login";
            }
        };
    }

    if (togglePwd) {
        togglePwd.onclick = () => {
            const pass = document.getElementById("password");
            if (pass) pass.type = pass.type === "password" ? "text" : "password";
        };
    }

    if (mainBtn) {
        mainBtn.onclick = () => {
            const email    = document.getElementById("email")?.value.trim();
            const password = document.getElementById("password")?.value.trim();
            const name     = document.getElementById("name")?.value.trim() || "";

            if (!msg) return;
            msg.style.color = "red";

            if (!email || !password || (!isLogin && !name)) { msg.innerText = "All fields required ❗"; return; }
            if (password.length < 6) { msg.innerText = "Password must be 6+ characters ❗"; return; }

            if (isLogin) {
                fetch('/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email, password })
                })
                .then(r => r.json())
                .then(data => {
                    if (data.name) {
                        msg.style.color = "green";
                        msg.innerText   = "Login Success ✅";
                        closePopup();

                        const navRight = document.getElementById("navRight");
                        if (navRight) {
                            navRight.innerHTML = `
                                <div class="icon-box premium-icon desktop-count-icon" tabindex="0" aria-label="Wishlist" onclick="window.location='/wishlist'">
                                    <i class="fa-solid fa-heart"></i>
                                    <span class="badge" id="wishlistCount">0</span>
                                </div>
                                <div class="icon-box premium-icon desktop-count-icon" tabindex="0" aria-label="Cart" onclick="window.location='/cart'">
                                    <i class="fa-solid fa-cart-shopping"></i>
                                    <span class="badge" id="cartCount">0</span>
                                </div>
                                <a href="/account" class="user-profile-link">
                                    <div class="avatar premium-avatar">${data.name.charAt(0)}</div>
                                </a>
                            `;
                        }

                        // Guest sync ONLY here, after login
                        const gCart = JSON.parse(localStorage.getItem("guestCart") || "[]");
                        const gWish = JSON.parse(localStorage.getItem("guestWishlist") || "[]");

                        if (gCart.length) {
                            fetch('/api/sync-guest-cart', {
                                method: 'POST', headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({ items: gCart })
                            }).then(() => { localStorage.removeItem("guestCart"); updateNavbarCounts(); });
                        }

                        if (gWish.length) {
                            fetch('/api/sync-guest-wishlist', {
                                method: 'POST', headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({ items: gWish })
                            }).then(() => { localStorage.removeItem("guestWishlist"); updateNavbarCounts(); });
                        }

                        updateNavbarCounts();
                        window.dispatchEvent(new Event("user-login"));
                        setTimeout(() => { if (msg) msg.innerText = ""; }, 1500);
                    } else {
                        msg.innerText = data.message || "Login failed";
                    }
                });
            } else {
                fetch('/register', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name, email, password })
                })
                .then(r => r.json())
                .then(data => {
                    if (data.message && data.message.toLowerCase().includes("success")) {
                        msg.style.color = "green";
                        msg.innerText   = "Registered Successfully ✅";
                        setTimeout(() => { if (switchBtn) switchBtn.click(); }, 1000);
                    } else {
                        msg.innerText = data.message || "Registration failed";
                    }
                });
            }
        };
    }
});

// ================= LOGIN CHECK =================
function isUserLoggedIn() {
    return document.querySelector(".avatar, .avatar-img") !== null;
}

// ================= NAVBAR COUNTS =================
function updateNavbarCounts() {
    if (isUserLoggedIn()) {
        fetch("/get_counts")
            .then(r => r.json())
            .then(d => {
                const c = document.getElementById("cartCount");
                const w = document.getElementById("wishlistCount");
                if (c) c.textContent = d.cart    || 0;
                if (w) w.textContent = d.wishlist || 0;
                syncNavbarBadgeVisibility();
            }).catch(() => {});
    } else {
        updateGuestCounts();
    }
}
window.addEventListener("user-login", updateNavbarCounts);

function syncNavbarBadgeVisibility() {
    document.querySelectorAll("#wishlistCount, #cartCount").forEach((badge) => {
        const count = Number.parseInt((badge.textContent || "0").trim(), 10) || 0;
        badge.classList.toggle("is-zero", count <= 0);
    });
}

document.addEventListener("DOMContentLoaded", syncNavbarBadgeVisibility);

// ================= GUEST HELPERS =================
function updateGuestCounts() {
    if (isUserLoggedIn()) return;
    const gCart = JSON.parse(localStorage.getItem("guestCart") || "[]");
    const gWish = JSON.parse(localStorage.getItem("guestWishlist") || "[]");
    const c = document.getElementById("cartCount");
    const w = document.getElementById("wishlistCount");
    if (c) c.textContent = gCart.reduce((s, i) => s + (i.qty || 1), 0);
    if (w) w.textContent = gWish.length;
    syncNavbarBadgeVisibility();
}

function showGuestToast(message) {
    let toast = document.getElementById("guestToast");
    if (!toast) {
        toast = document.createElement("div");
        toast.id = "guestToast";
        toast.style.cssText = "position:fixed;bottom:80px;left:50%;transform:translateX(-50%);background:#333;color:#fff;padding:10px 20px;border-radius:20px;font-size:14px;z-index:9999;opacity:0;transition:opacity 0.3s;white-space:nowrap;pointer-events:none;";
        document.body.appendChild(toast);
    }
    toast.innerText = message;
    toast.style.opacity = "1";
    setTimeout(() => { toast.style.opacity = "0"; }, 2500);
}

function isInGuestWishlist(productId, colorId = null) {
    const list = JSON.parse(localStorage.getItem("guestWishlist") || "[]");
    return list.some(i => String(i.productId) === String(productId) &&
                          String(i.colorId  || null) === String(colorId || null));
}

function isInGuestCart(productId, colorId = null) {
    const list = JSON.parse(localStorage.getItem("guestCart") || "[]");
    return list.some(i => String(i.productId) === String(productId) &&
                          String(i.colorId  || null) === String(colorId || null));
}

// ================= CART =================
function addToCart(productId, colorId = null, sizeId = null) {
    if (isUserLoggedIn()) {
        fetch(`/cart/toggle/${productId}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ color_id: colorId, size_id: sizeId })
        })
        .then(r => r.json())
        .then(data => {
            const el = document.getElementById("cartCount");
            if (el && data.count != null) el.innerText = data.count;
            syncNavbarBadgeVisibility();
            showGuestToast("Added to cart! 🛒");
        }).catch(() => {});
    } else {
        addToGuestCart(productId, colorId, sizeId);
    }
}

// Alias used by products.html
function addToGuestCart(productId, colorId = null, sizeId = null) {
    let gCart = JSON.parse(localStorage.getItem("guestCart") || "[]");
    const existing = gCart.find(i =>
        String(i.productId) === String(productId) &&
        String(i.colorId || null) === String(colorId || null));
    if (existing) { existing.qty = (existing.qty || 1) + 1; }
    else { gCart.push({ productId, colorId, sizeId, qty: 1 }); }
    localStorage.setItem("guestCart", JSON.stringify(gCart));
    updateGuestCounts();
    showGuestToast("Added to cart! Login to checkout 🛒");
}

// ================= WISHLIST =================
function addToWishlist(productId, btn = null, colorId = null) {
    if (isUserLoggedIn()) {
        fetch(`/wishlist/toggle/${productId}${colorId ? `?color_id=${colorId}` : ""}`)
        .then(r => r.json())
        .then(data => {
            if (data.error) return;
            if (btn) { btn.classList.toggle("active", data.in_wishlist); btn.innerHTML = data.in_wishlist ? "❤️" : "♡"; }
            const w = document.getElementById("wishlistCount");
            if (w) w.innerText = data.count;
            syncNavbarBadgeVisibility();
        }).catch(err => console.error("Wishlist error:", err));
    } else {
        let gWish = JSON.parse(localStorage.getItem("guestWishlist") || "[]");
        const idx = gWish.findIndex(i =>
            String(i.productId) === String(productId) &&
            String(i.colorId || null) === String(colorId || null));
        let inWishlist;
        if (idx > -1) { gWish.splice(idx, 1); inWishlist = false; }
        else          { gWish.push({ productId, colorId }); inWishlist = true; }
        localStorage.setItem("guestWishlist", JSON.stringify(gWish));
        if (btn) { btn.classList.toggle("active", inWishlist); btn.innerHTML = inWishlist ? "❤️" : "♡"; }
        updateGuestCounts();
        showGuestToast(inWishlist ? "Saved to wishlist! Login to sync ❤️" : "Removed from wishlist");
    }
}

function checkWishlist(productId, colorId = null) {
    if (!isUserLoggedIn()) return Promise.resolve(isInGuestWishlist(productId, colorId));
    return fetch(`/wishlist/check/${productId}${colorId ? `?color_id=${colorId}` : ""}`)
        .then(r => r.json()).then(d => d.in_wishlist).catch(() => false);
}

// ================= PRODUCT HELPERS =================
function getProductBaseId(p)    { return p.product_id || p.id; }
function getProductColorId(p)   { return p.color_variant?.id || p.colors?.[0]?.id || null; }
function getProductDetailUrl(p) {
    const pid = getProductBaseId(p), cid = getProductColorId(p);
    return cid ? `/product/${pid}?color=${cid}` : `/product/${pid}`;
}

// ================= HOMEPAGE PRODUCTS =================
function loadProducts() {
    fetch("/products")
        .then(r => r.json())
        .then(data => {
            // index.html has BOTH <section id="products"> and <div id="products" class="product-container">
            // We want the .product-container div
            const container = document.querySelector(".product-container") || document.getElementById("products");
            if (!container) return;
            container.innerHTML = "";

            const featuredProducts = Array.from(data.reduce((items, product) => {
                const productId = getProductBaseId(product);
                const current = items.get(productId) || {
                    ...product,
                    id: productId,
                    product_id: productId,
                    colors: [],
                    color_images: {},
                    images: product.images || []
                };
                const variantColor = product.color_variant || product.colors?.[0] || null;
                const availableColors = product.colors?.length ? product.colors : (variantColor ? [variantColor] : []);

                availableColors.forEach(color => {
                    if (color?.id && color?.code && !current.colors.some(item => String(item.id) === String(color.id))) {
                        current.colors.push(color);
                    }
                });

                if (variantColor?.id && product.images?.length) {
                    current.color_images[variantColor.id] = product.images;
                }

                if (product.color_images) {
                    current.color_images = { ...current.color_images, ...product.color_images };
                }

                if ((!current.images || !current.images.length) && product.images?.length) {
                    current.images = product.images;
                }

                items.set(productId, current);
                return items;
            }, new Map()).values());

            featuredProducts.slice(0, 4).forEach(product => {
                const productId    = getProductBaseId(product);
                const variantColor = product.color_variant || product.colors?.[0] || null;
                const colorId      = variantColor?.id || null;
                const image        = product.images?.[0] || "/static/images/default.png";
                const colorList    = (product.colors?.length ? product.colors : (variantColor ? [variantColor] : []))
                    .filter(color => color?.id && color?.code);

                const ratingHTML   = product.rating ? `<div class="rating">⭐ ${product.rating}</div>` : "";
                const discountHTML = product.discount_percent > 0 ? `<span class="discount-badge">-${product.discount_percent}%</span>` : "";
                const oldPriceHTML = product.original_price ? `<span class="old-price">₹${product.original_price}</span>` : "";
                const colorsHTML   = colorList.length
                    ? `<div class="color-options">${colorList.map((color, index) => `
                        <span
                            class="color-circle${index === 0 ? " active" : ""}"
                            style="background:${color.code}"
                            title="${color.name || "Color"}"
                            data-color="${color.id}"
                            data-product="${productId}">
                        </span>
                    `).join("")}</div>`
                    : "";

                const div = document.createElement("div");
                div.className = "product-card";
                div.innerHTML = `
                    <div class="product-image-wrapper">
                        ${discountHTML}
                        <img class="product-img" src="${image}" alt="${product.name}">
                    </div>
                    <div class="product-info">
                        ${colorsHTML}
                        <h4>${product.name}</h4>
                        ${ratingHTML}
                        <div class="price-box">
                            <span class="new-price">₹${product.price}</span>
                            ${oldPriceHTML}
                        </div>
                    </div>
                `;

                const imgEl       = div.querySelector(".product-img");

                div.querySelectorAll(".color-circle").forEach(circle => {
                    circle.addEventListener("mouseenter", () => {
                        div.querySelectorAll(".color-circle").forEach(item => item.classList.remove("active"));
                        circle.classList.add("active");
                        const imgs = product.color_images?.[circle.dataset.color];
                        if (imgs?.length) imgEl.src = imgs[0];
                    });
                    circle.addEventListener("mouseleave", () => { imgEl.src = image; });
                    circle.addEventListener("click", e => {
                        e.stopPropagation();
                        window.location.href = `/product/${circle.dataset.product}?color=${circle.dataset.color}`;
                    });
                });

                div.addEventListener("click", () => { window.location.href = getProductDetailUrl(product); });

                container.appendChild(div);
            });
        })
        .catch(err => console.error("Product load error:", err));
}

// ================= LOGIN-GATED ACTIONS =================
window.handleBuyNow = function (productId, colorId, sizeId) {
    if (!isUserLoggedIn()) { openPopup(); return; }
    addToCart(productId, colorId, sizeId);
    window.location.href = "/cart";
};

window.handleCheckout = function () {
    if (!isUserLoggedIn()) { openPopup(); return; }
    window.location.href = "/checkout";
};

window.handleAccountClick = function (e) {
    if (e) e.preventDefault();
    if (!isUserLoggedIn()) { openPopup(); } else { window.location.href = "/account"; }
};

// ================= DROPDOWN =================
function toggleDropdown() {
    const m = document.getElementById("dropdownMenu");
    if (m) m.classList.toggle("show");
}
window.addEventListener("click", e => {
    if (!e.target.closest(".user-dropdown")) {
        const m = document.getElementById("dropdownMenu");
        if (m) m.classList.remove("show");
    }
});

// ================= LIVE SEARCH =================
document.addEventListener("DOMContentLoaded", () => {
    const searchFields = [
        { input: document.getElementById("searchInput"),       dropdown: document.getElementById("searchDropdown") },
        { input: document.getElementById("mobileSearchInput"), dropdown: document.getElementById("mobileSearchDropdown") }
    ].filter(f => f.input && f.dropdown);

    searchFields.forEach(({ input, dropdown }) => {
        input.addEventListener("input", function () {
            const q = this.value.trim();
            if (!q) { dropdown.style.display = "none"; return; }
            fetch("/api/search?q=" + encodeURIComponent(q))
            .then(r => r.json())
            .then(data => {
                dropdown.innerHTML = "";
                if (!data.length) { dropdown.innerHTML = "<p style='padding:10px;'>No results found</p>"; dropdown.style.display = "block"; return; }
                data.forEach(p => {
                    const d = document.createElement("div");
                    d.className = "search-item";
                    d.innerHTML = `<img src="${p.image}"><div><b>${p.name}</b><br>₹${p.price}</div>`;
                    d.onclick = () => { window.location.href = "/product/" + p.id; };
                    dropdown.appendChild(d);
                });
                dropdown.style.display = "block";
            });
        });
    });

    window.addEventListener("click", e => {
        if (!e.target.closest(".search-bar") && !e.target.closest(".mobile-search-card") && !e.target.closest(".mobile-search-toggle")) {
            searchFields.forEach(({ dropdown }) => { dropdown.style.display = "none"; });
        }
    });
});

// ================= FAQ =================
document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll(".faq-item").forEach(item => {
        item.addEventListener("click", () => item.classList.toggle("active"));
    });
});

// ================= CONTACT =================
function sendMessage(e) { e.preventDefault(); alert("Message sent successfully! ✅"); }

// ================= MAGNETIC ICON =================
document.querySelectorAll(".premium-icon").forEach(icon => {
    icon.addEventListener("mousemove", e => {
        const r = icon.getBoundingClientRect();
        icon.style.transform = `translate(${(e.clientX - r.left - r.width/2) * 0.2}px, ${(e.clientY - r.top - r.height/2) * 0.2}px) scale(1.15)`;
    });
    icon.addEventListener("mouseleave", () => { icon.style.transform = "translate(0,0) scale(1)"; });
});

// ================= LOADER =================
window.addEventListener("load", () => {
    const loader = document.getElementById("loader");
    if (!loader) return;
    if (!sessionStorage.getItem("loaderShown")) {
        sessionStorage.setItem("loaderShown", "true");
        setTimeout(() => { loader.classList.add("fade"); setTimeout(() => { loader.style.display = "none"; }, 1000); }, 2500);
    } else { loader.style.display = "none"; }
});

// ================= INIT =================
document.addEventListener("DOMContentLoaded", () => {
    updateNavbarCounts();
    updateGuestCounts();
    setTimeout(loadProducts, 100);
});
// ❌ NO auto-sync on page load — only in login success block above
