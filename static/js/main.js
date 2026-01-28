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

	const isOpen = () => burger.getAttribute('aria-expanded') === 'true';

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
		isOpen() ? close() : open();
	});

	// Alguns celulares são mais confiáveis com pointer/touch do que click
	overlay.addEventListener('pointerdown', close);
	overlay.addEventListener('click', close);
	if (closeBtn) {
		closeBtn.addEventListener('pointerdown', close);
		closeBtn.addEventListener('click', close);
	}
	if (drawerLinks && drawerLinks.length) {
		drawerLinks.forEach((a) => a.addEventListener('click', close));
	}

	// Fallback: clique fora do drawer fecha (mesmo se o overlay não capturar o evento)
	document.addEventListener(
		'click',
		(e) => {
			if (!isOpen()) return;
			const target = e.target;
			if (!(target instanceof Element)) return;
			if (drawer.contains(target)) return;
			if (burger.contains(target)) return;
			close();
		},
		true
	);

	document.addEventListener('keydown', (e) => {
		if (e.key === 'Escape' && isOpen()) {
			close();
		}
	});
});