document.addEventListener('DOMContentLoaded', () => {
	const burger = document.querySelector('.topbar-burger');
	const drawer = document.getElementById('mobile-drawer');
	const overlay = document.getElementById('drawer-overlay');
	const closeBtn = drawer ? drawer.querySelector('.drawer-close') : null;
	const drawerLinks = drawer ? drawer.querySelectorAll('a') : [];

	if (!burger || !drawer || !overlay) return;

	const setOpen = (open) => {
		burger.setAttribute('aria-expanded', open ? 'true' : 'false');
		drawer.hidden = !open;
		overlay.hidden = !open;
		document.documentElement.classList.toggle('drawer-open', open);
	};

	const open = () => {
		setOpen(true);
		// foco no botão fechar para acessibilidade
		if (closeBtn) closeBtn.focus();
	};

	const close = () => {
		setOpen(false);
		burger.focus();
	};

	burger.addEventListener('click', () => {
		const isOpen = burger.getAttribute('aria-expanded') === 'true';
		isOpen ? close() : open();
	});

	overlay.addEventListener('click', close);
	if (closeBtn) closeBtn.addEventListener('click', close);
	if (drawerLinks && drawerLinks.length) {
		drawerLinks.forEach((a) => a.addEventListener('click', close));
	}

	document.addEventListener('keydown', (e) => {
		if (e.key === 'Escape' && burger.getAttribute('aria-expanded') === 'true') {
			close();
		}
	});
});