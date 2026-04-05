// ================= INIT =================
window.onload = function () {

    const popup = document.getElementById("popup");
    const blurBg = document.getElementById("blurBg");
    const loginBtn = document.getElementById("loginBtn");

    function openPopup() {
        if (popup && blurBg) {
            popup.classList.add("show");
            blurBg.style.display = "block";
            document.body.style.overflow="hidden";
        }
    }

    function closePopup() {
        if (popup && blurBg) {
            popup.classList.remove("show");
            blurBg.style.display = "none";
            document.body.style.overflow="";
        }
    }
 // ✅ AUTO POPUP AFTER 3 SEC (ONLY IF NOT LOGGED IN)
    const isLoggedIn = document.querySelector(".avatar") !== null;

    if (!isLoggedIn) {
        setTimeout(() => {
            openPopup();
        }, 3000);
    }
    // AUTO SHOW AFTER 3s (ONLY IF USER NOT LOGGED IN)
    if (loginBtn) {
        loginBtn.addEventListener("click", function(e) {
            e.preventDefault();
            openPopup();
        });
    }
    if (!isLoggedIn) {
    setTimeout(openPopup, 3000);
}

   

    // CLOSE BUTTON
    const closeBtn = document.getElementById("closeBtn");
    if (closeBtn) closeBtn.onclick = closePopup;

    // LOAD PRODUCTS
    loadProducts();
};

function handleAccountClick(e) {
    const isLoggedIn = document.querySelector(".avatar") !== null;

    if (!isLoggedIn) {
        e.preventDefault();
        openPopup();
    } else {
        window.location.href = "/account";
    }
}



let slides = document.querySelectorAll(".slide");
let index = 0;

setInterval(() => {
    slides[index].classList.remove("active");
    index = (index + 1) % slides.length;
    slides[index].classList.add("active");
}, 4000);

// ================= REGISTER =================
function register() {
    fetch('/register', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            name: document.getElementById("name").value,
            email: document.getElementById("email").value,
            password: document.getElementById("password").value
        })
    })
    .then(res => res.json())
    .then(data => {
        alert(data.message);
    });
}

// ================= LOGIN =================
function login() {
    fetch('/login', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            email: document.getElementById("email").value,
            password: document.getElementById("password").value
        })
    })
    .then(res => res.json())
    .then(data => {
        alert(data.message);

        if (data.name) {
            alert("Login Success ✅");
            location.reload(); // show avatar after login
        }
    });
}

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

function updateNavbarCounts() {
    fetch("/get_counts")
    .then(res => res.json())
    .then(data => {
        document.getElementById("cartCount").innerText = data.cart;
        document.getElementById("wishlistCount").innerText = data.wishlist;
    })
    .catch(err => console.error("Count error:", err));
}

// LOAD ON PAGE
document.addEventListener("DOMContentLoaded", () => {
    updateNavbarCounts();
});
// ADD TO CART
function addToCart(productId) {
    const isLoggedIn = document.querySelector(".avatar") !== null;

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
function addToWishlist(productId) {
    const isLoggedIn = document.querySelector(".avatar") !== null;

    if (!isLoggedIn) {
        openPopup();
        return;
    }

    fetch(`/add_to_wishlist/${productId}`)
    .then(res => res.json())
    .then(data => {
        document.getElementById("wishlistCount").innerText = data.count;
    });
}

// REMOVE ITEM (optional)
function removeFromCart(index) {
    let cart = getCart();
    cart.splice(index, 1);
    localStorage.setItem("cart", JSON.stringify(cart));
    updateNavbarCounts();
}

// LOAD ON PAGE START
document.addEventListener("DOMContentLoaded", () => {
    updateNavbarCounts();
});

function loadProducts() {
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

        data.slice(0, 4).forEach(product => {

            const image = product.images.length > 0 
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

/* ✅ CALL FUNCTION AFTER PAGE LOAD */
document.addEventListener("DOMContentLoaded", loadProducts);

// ================= 🔍 LIVE SEARCH =================
const searchInput = document.getElementById("searchInput");
const dropdown = document.getElementById("searchDropdown");

if (searchInput) {

    searchInput.addEventListener("input", function () {

        const query = this.value;

        if (query.length < 1) {
            dropdown.style.display = "none";
            return;
        }

        // ✅ CALL BACKEND SEARCH API
        fetch("/api/search?q=" + query)
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

    // CLOSE DROPDOWN
    document.addEventListener("click", (e) => {
        if (!e.target.closest(".search-bar")) {
            dropdown.style.display = "none";
        }
    });
}

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