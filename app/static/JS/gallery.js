function showSidebar(){
    const sidebar = document.querySelector(`.sidebar`);
    sidebar.style.display = 'flex'
}

function hideSidebar() {
    const sidebar = document.querySelector(`.sidebar`);
    sidebar.style.display = 'none'
}

document.querySelectorAll('.carousel-item').forEach(item => {
    item.addEventListener('click', () => {
        const carousels = item.closest('.carousels');
        const isActive = item.classList.contains('active');

        // Remove active from all items in this carousel
        carousels.querySelectorAll('.carousel-item').forEach(i => i.classList.remove('active'));

        if (isActive) {
            // Second click — unpause
            carousels.classList.remove('paused');
        } else {
            // First click — pause and show desc
            item.classList.add('active');
            carousels.classList.add('paused');
        }
    });
});