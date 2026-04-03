function showSection(id) {
    document.querySelectorAll('.section').forEach(sec => {
        sec.classList.remove('active');
    });

    document.getElementById(id).classList.add('active');

    if (id === "orders") loadOrders();
    if (id === "wishlist") loadWishlist();
}


// LOAD ORDERS
function loadOrders() {
    fetch('/get_orders')
    .then(res => res.json())
    .then(data => {
        let html = "";

        data.forEach(order => {
            html += `
                <div>
                    <p>${order.product_name} - ₹${order.price}</p>
                    <small>Status: ${order.status}</small>
                </div>
            `;
        });

        document.getElementById("ordersList").innerHTML = html;
    });
}


// LOAD WISHLIST
function loadWishlist() {
    fetch('/get_wishlist')
    .then(res => res.json())
    .then(data => {
        let html = "";

        data.forEach(item => {
            html += `<p>${item.product_name}</p>`;
        });

        document.getElementById("wishlistList").innerHTML = html;
    });
}