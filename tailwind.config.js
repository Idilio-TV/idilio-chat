import typography from '@tailwindcss/typography';
import containerQueries from '@tailwindcss/container-queries';

/** @type {import('tailwindcss').Config} */
export default {
	darkMode: 'class',
	content: ['./src/**/*.{html,js,svelte,ts}'],
	theme: {
		extend: {
			colors: {
				// Idilio brand accent (purple/magenta pair from idilio-dashboard's
				// Sidebar.tsx: #6614e7 / #d25af0), remapped onto Tailwind's `blue`
				// scale rather than a new color name -- `blue-*` is what this app
				// already uses everywhere for accents/highlights/active states
				// (see CalendarView.svelte, Message.svelte's active outline, link
				// colors), so overriding it here recolors those call sites without
				// touching every component individually. `gray` is left alone --
				// idilio-dashboard's own bg-gray-950/bg-gray-800 are stock Tailwind
				// gray too, unmodified; the brand only shows up as an accent on
				// top of ordinary neutrals, not a tinted neutral scale.
				blue: {
					50: '#faf5ff',
					100: '#f3e6fe',
					200: '#e9ccfc',
					300: '#dda0fa',
					400: '#d25af0',
					500: '#a730e0',
					600: '#6614e7',
					700: '#560fc4',
					800: '#470da0',
					900: '#390a80',
					950: '#22054d'
				}
			},
			typography: {
				DEFAULT: {
					css: {
						pre: false,
						code: false,
						'pre code': false,
						'code::before': false,
						'code::after': false
					}
				}
			},
			padding: {
				'safe-bottom': 'env(safe-area-inset-bottom)'
			},
			transitionProperty: {
				width: 'width'
			}
		}
	},
	plugins: [typography, containerQueries]
};
