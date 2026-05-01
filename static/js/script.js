document.addEventListener("DOMContentLoaded", function () {

    const popup = document.getElementById("popup");
    const blurBg = document.getElementById("blurBg");
    const loginBtn = document.getElementById("loginBtn");

    const switchBtn = document.getElementById("switchMode");
    const nameField = document.getElementById("name");
    const title = document.getElementById("formTitle");
    const mainBtn = document.getElementById("mainBtn");
    const msg = document.getElementById("formMsg");
    const togglePassword = document.getElementById("togglePassword");

    let isLogin = true;

    // OPEN
    window.openPopup = function () {
        popup.classList.add("show");
        blurBg.style.display = "block";
        document.body.style.overflow = "hidden";
    };

    // CLOSE
    window.closePopup = function () {
        popup.classList.remove("show");
        blurBg.style.display = "none";
        document.body.style.overflow = "";
    };

    // AUTO POPUP
    const isLoggedIn = document.querySelector(".avatar, .avatar-img") !== null;

    if (!isLoggedIn) {
        setTimeout(openPopup, 3000);
    }

    // LOGIN BTN
    if (loginBtn) {
        loginBtn.addEventListener("click", function (e) {
            e.preventDefault();
            openPopup();
        });
    }

    // CLOSE BTN
    document.getElementById("closeBtn").onclick = closePopup;

    // TOGGLE LOGIN/REGISTER
    switchBtn.onclick = () => {
        isLogin = !isLogin;
        msg.innerText = "";

        if (isLogin) {
            title.innerText = "Login";
            nameField.style.display = "none";
            mainBtn.innerText = "Login";
            switchBtn.innerText = "Create Account";
        } else {
            title.innerText = "Register";
            nameField.style.display = "block";
            mainBtn.innerText = "Register";
            switchBtn.innerText = "Login";
        }
    };

    // PASSWORD EYE
    togglePassword.onclick = () => {
        const pass = document.getElementById("password");
        pass.type = pass.type === "password" ? "text" : "password";
    };

    // MAIN BUTTON
    mainBtn.onclick = () => {

        const email = document.getElementById("email").value.trim();
        const password = document.getElementById("password").value.trim();
        const name = document.getElementById("name").value.trim();

        msg.style.color = "red";

        if (!email || !password || (!isLogin && !name)) {
            msg.innerText = "All fields required ❗";
            return;
        }

        if (password.length < 6) {
            msg.innerText = "Password must be 6+ characters ❗";
            return;
        }

       if (isLogin) {

    fetch('/login', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ email, password })
    })
    .then(res => res.json())
    .then(data => {

        if (data.name) {
            msg.style.color = "green";
            msg.innerText = "Login Success ✅";

            window.dispatchEvent(new Event("user-login"));
            closePopup();

            const navRight = document.getElementById("navRight");

            navRight.innerHTML = `
                <div class="icon-box premium-icon" onclick="window.location='/wishlist'">
                    <i class="fa-solid fa-heart"></i>
                    <span class="badge" id="wishlistCount">0</span>
                </div>

                <div class="icon-box premium-icon" onclick="window.location='/cart'">
                    <i class="fa-solid fa-cart-shopping"></i>
                    <span class="badge" id="cartCount">0</span>
                </div>

                <a href="/account" class="user-profile-link">
                    <div class="avatar premium-avatar">
                        ${data.name.charAt(0)}
                    </div>
                </a>
            `;

            if (typeof updateNavbarCounts === "function") {
                updateNavbarCounts();
            }

            setTimeout(() => {
                msg.innerText = "";
            }, 1000);

        } else {
            msg.innerText = data.message;
        }

    });

} else {

    fetch('/register', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ name, email, password })
    })
    .then(res => res.json())
    .then(data => {

        if (data.message.includes("success")) {
            msg.style.color = "green";
            msg.innerText = "Registered Successfully ✅";

            setTimeout(() => {
                switchBtn.click();
            }, 1000);
        } else {
            msg.innerText = data.message;
        }

    });

}
};
});
window.addEventListener("user-login", () => {
    updateNavbarCounts();
});

// ================= DROPDOWN =================
function toggleDropdown() {
    const menu = document.getElementById("dropdownMenu");
    if (menu) {
        menu.classList.toggle("show");
    }
}

// CLOSE DROPDOWN OUTSIDE CLICK
window.addEventListener("click", function(e) {
    if (!e.target.closest('.user-dropdown')) {
        const menu = document.getElementById("dropdownMenu");
        if (menu) menu.classList.remove("show");
    }
});

// ================= NAVIGATION =================
// =======================
// 🛒 CART + ❤️ WISHLIST SYSTEM
// =======================


// LOAD ON PAGE

// ADD TO CART
function addToCart(productId) {
    const isLoggedIn = document.querySelector(".avatar, .avatar-img") !== null;

    if (!isLoggedIn) {
        openPopup();
        return;
    }

    fetch(`/add_to_cart/${productId}`)
    .then(res => res.json())
    .then(data => {
        document.getElementById("cartCount").innerText = data.count;
    });
}

// ADD TO WISHLIST
/*
function addToWishlist(productId, btn = null, colorId = null) {
    const isLoggedIn = document.querySelector(".avatar, .avatar-img") !== null;

    if (!isLoggedIn) {
        openPopup();
        return;
    }

    fetch(`/add_to_wishlist/${productId}`)
    .then(res => res.json())
    .then(data => {
        document.getElementById("wishlistCount").innerText = data.count;
    });
}*/
function addToWishlist(productId, btn = null, colorId = null) {
    const isLoggedIn = document.querySelector(".avatar, .avatar-img") !== null;

    if (!isLoggedIn) {
        openPopup();
        return;
    }

    fetch(`/wishlist/toggle/${productId}${colorId ? `?color_id=${colorId}` : ""}`)
    .then(res => res.json())
    .then(data => {

        if (data.error) return;

        // ❤️ BUTTON UPDATE (if exists)
        if (btn) {
            if (data.in_wishlist) {
                btn.classList.add("active");
                btn.innerHTML = "❤️";
            } else {
                btn.classList.remove("active");
                btn.innerHTML = "♡";
            }
        }

        // 🔥 NAVBAR COUNT UPDATE
        const wishlistCount = document.getElementById("wishlistCount");
        if (wishlistCount) {
            wishlistCount.innerText = data.count;
        }
    })
    .catch(err => console.error("Wishlist error:", err));
}

// REMOVE ITEM (optional)




/*function loadProducts() {
    fetch("/products")
    .then(res => res.json())
    .then(data => {
         
        console.log("Products:", data);
        const container = document.getElementById("products");

        if (!container) {
            console.error("Container not found");
            return;
        }

        container.innerHTML = "";

        data.slice(0, 6).forEach(product => {

            const image = product.images && product.images.length > 0 
                ? product.images[0] 
                : "/static/images/default.png"; // fallback image

            const div = document.createElement("div");
            div.className = "product-card";

            div.innerHTML = `
                <img src="${image}" style="width:100%; height:200px; object-fit:cover;">
                <h4>${product.name}</h4>
                <p>₹${product.price}</p>
            `;

            div.onclick = () => {
                window.location.href = "/product/" + product.id;
            };

            container.appendChild(div);
        });
    })
    .catch(err => console.error("Product load error:", err));
}
function loadProducts() {
    fetch("/products")
        .then(res => res.json())
        .then(data => {
            const container = document.getElementById("products");

            if (!container) {
                console.error("Container not found");
                return;
            }

            container.innerHTML = "";

            data.slice(0, 4).forEach(product => {
                const image =
                    product.images && product.images.length > 0
                        ? product.images[0]
                        : "/static/images/default.png";

                const rating = product.rating
                    ? `⭐ ${product.rating}`
                    : "";

                const discountHTML = product.discount_percent > 0
                    ? `<span class="discount-badge">-${product.discount_percent}%</span>`
                    : "";

                const oldPriceHTML = product.original_price
                    ? `<span class="old-price">₹${product.original_price}</span>`
                    : "";

                const div = document.createElement("div");
                div.className = "product-card";

                div.innerHTML = `
                    <div class="product-image-wrapper">
                        <span class="discount-badge">-${discountHTML}%</span>

                        <button class="wishlist-btn" data-id="${product.id}">
                            ♡
                        </button>

                        <img src="${image}" alt="${product.name}">
                    </div>

                    <div class="product-info">
                        

                        <h4>${product.name}</h4>

                        ${rating ? `<div class="rating">${rating}</div>` : ""}

                        <div class="price-box">
                            <span class="new-price">₹${product.price}</span>
                            <span class="old-price">₹${oldPriceHTML}</span>
                        </div>
                    </div>
                `;

                // Product page redirect
                div.addEventListener("click", () => {
                    window.location.href = "/product/" + product.id;
                });

                // Wishlist click
                const wishlistBtn = div.querySelector(".wishlist-btn");

                wishlistBtn.addEventListener("click", (e) => {
                    e.stopPropagation(); // card redirect stop

                    addToWishlist(product.id, wishlistBtn);
                });

                container.appendChild(div);
            });
        })
        .catch(err => console.error("Product load error:", err));
}
*/
// ✅ OUTSIDE (global)
function checkWishlist(productId, colorId = null) {
    return fetch(`/wishlist/check/${productId}${colorId ? `?color_id=${colorId}` : ""}`)
        .then(res => res.json())
        .then(data => data.in_wishlist)
        .catch(() => false);
}

function getProductBaseId(product) {
    return product.product_id || product.id;
}

function getProductColorId(product) {
    return product.color_variant?.id || product.colors?.[0]?.id || null;
}

function getProductDetailUrl(product) {
    const productId = getProductBaseId(product);
    const colorId = getProductColorId(product);

    return colorId
        ? `/product/${productId}?color=${colorId}`
        : `/product/${productId}`;
}


// ✅ MAIN FUNCTION
function loadProducts() {
    fetch("/products")
        .then(res => res.json())
        .then(data => {
            console.log(data) 
            const container = document.getElementById("products");
            if (!container) return;

            container.innerHTML = "";

            data.slice(0, 4).forEach(product => {

                const productId = getProductBaseId(product);
                const variantColor = product.color_variant || product.colors?.[0] || null;
                const colorId = variantColor?.id || null;
                const image = product.images?.[0] || "/static/images/default.png";

                const ratingHTML = product.rating
                    ? `<div class="rating">⭐ ${product.rating}</div>`
                    : "";

                const discountHTML = product.discount_percent > 0
                    ? `<span class="discount-badge">-${product.discount_percent}%</span>`
                    : "";

                const oldPriceHTML = product.original_price
                    ? `<span class="old-price">₹${product.original_price}</span>`
                    : "";

                // ✅ COLORS
                const colorsHTML = variantColor
                    ? `<div class="color-options">
                        <span 
                            class="color-circle"
                            style="background:${variantColor.code}"
                            title="${variantColor.name}"
                            data-color="${variantColor.id}"
                            data-product="${productId}"
                        ></span>
                       </div>`
                    : "";

                const div = document.createElement("div");
                div.className = "product-card";

                div.innerHTML = `
                    <div class="product-image-wrapper">
                        ${discountHTML}

                        <button class="wishlist-btn" data-id="${productId}">
                            ♡
                        </button>

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

                const wishlistBtn = div.querySelector(".wishlist-btn");
                const imgEl = div.querySelector(".product-img");

                /* =============================
                   AMAZON STYLE HOVER CHANGE
                ==============================*/
                div.querySelectorAll(".color-circle").forEach(circle => {

                    circle.addEventListener("mouseenter", (e) => {
                        e.stopPropagation();

                        const colorId = circle.dataset.color;

                        const colorImages = product.color_images?.[colorId];

                        if (colorImages && colorImages.length > 0) {
                            imgEl.src = colorImages[0];
                        }
                    });

                    circle.addEventListener("mouseleave", () => {
                        imgEl.src = image;
                    });

                    /* =============================
                       CLICK → OPEN PRODUCT COLOR
                    ==============================*/
                    circle.addEventListener("click", (e) => {
                        e.stopPropagation();

                        const productId = circle.dataset.product;
                        const colorId = circle.dataset.color;

                        // 👉 IMPORTANT FIX (WORKING ROUTE)
                        window.location.href = `/product/${productId}?color=${colorId}`;
                    });
                });

                /* ================= PRODUCT CLICK ================= */
                div.addEventListener("click", () => {
                    window.location.href = getProductDetailUrl(product);
                });

                /* ================= WISHLIST ================= */
                checkWishlist(productId, colorId).then(inWishlist => {
                    if (inWishlist) {
                        wishlistBtn.classList.add("active");
                        wishlistBtn.innerHTML = "❤️";
                    }
                });

                wishlistBtn.addEventListener("click", (e) => {
                    e.stopPropagation();

                    addToWishlist(productId, wishlistBtn, colorId);

                    wishlistBtn.classList.toggle("active");
                    wishlistBtn.innerHTML = wishlistBtn.classList.contains("active")
                        ? "❤️"
                        : "♡";
                });

                container.appendChild(div);
            });
        })
        .catch(err => console.error("Product load error:", err));
}

/* INIT */
document.addEventListener("DOMContentLoaded", () => {
    updateNavbarCounts();
    loadProducts();
});
/* ✅ CALL FUNCTION AFTER PAGE LOAD */


// ================= 🔍 LIVE SEARCH =================
const searchFields = [
    { input: document.getElementById("searchInput"), dropdown: document.getElementById("searchDropdown") },
    { input: document.getElementById("mobileSearchInput"), dropdown: document.getElementById("mobileSearchDropdown") }
].filter(field => field.input && field.dropdown);

searchFields.forEach(({ input, dropdown }) => {
    input.addEventListener("input", function () {
        const query = this.value;

        if (query.length < 1) {
            dropdown.style.display = "none";
            return;
        }

        // ✅ CALL BACKEND SEARCH API
        fetch("/api/search?q=" + encodeURIComponent(query))
        .then(res => res.json())
        .then(data => {
            dropdown.innerHTML = "";

            if (data.length === 0) {
                dropdown.innerHTML = "<p style='padding:10px;'>No results found</p>";
                dropdown.style.display = "block";
                return;
            }

            data.forEach(product => {
                const div = document.createElement("div");
                div.className = "search-item";

                div.innerHTML = `
                    <img src="${product.image}">
                    <div>
                        <b>${product.name}</b><br>
                        ₹${product.price}
                    </div>
                `;

                div.onclick = () => {
                    window.location.href = "/product/" + product.id;
                };

                dropdown.appendChild(div);
            });

            dropdown.style.display = "block";
        });
    });
});

// CLOSE DROPDOWN
window.addEventListener("click", (e) => {
    if (!e.target.closest(".search-bar") && !e.target.closest(".mobile-search-card") && !e.target.closest(".mobile-search-toggle")) {
        searchFields.forEach(({ dropdown }) => {
            dropdown.style.display = "none";
        });
    }
});

function sendMessage(e) {
    e.preventDefault();
    alert("Message sent successfully! ✅");
}
// ================= FAQ =================
document.addEventListener("DOMContentLoaded", () => {
    const faqItems = document.querySelectorAll(".faq-item");

    faqItems.forEach(item => {
        item.addEventListener("click", () => {
            item.classList.toggle("active");
        });
    });
});

// 🧲 MAGNETIC ICON EFFECT
document.querySelectorAll(".premium-icon").forEach(icon => {
    icon.addEventListener("mousemove", e => {
        const rect = icon.getBoundingClientRect();
        const x = e.clientX - rect.left - rect.width / 2;
        const y = e.clientY - rect.top - rect.height / 2;

        icon.style.transform = `translate(${x*0.2}px, ${y*0.2}px) scale(1.15)`;
    });

    icon.addEventListener("mouseleave", () => {
        icon.style.transform = "translate(0,0) scale(1)";
    });
});

window.addEventListener('load', () => {
    const loader = document.getElementById('loader');

    if (!sessionStorage.getItem('loaderShown')) {
        sessionStorage.setItem('loaderShown', 'true');

        setTimeout(() => {
            loader.classList.add('fade');
            setTimeout(() => { loader.style.display = 'none'; }, 1000);
        }, 2500); 
    } else {
        loader.style.display = 'none';
    }
});
    
