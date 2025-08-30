import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// Dev server proxy so relative fetch('/rag/query') hits FastAPI (port 8000) instead of Vite
export default defineConfig({
	plugins: [react()],
	server: {
		port: 5174,
		host: true,
		proxy: {
			'/rag': 'http://localhost:8000',
			'/metrics': 'http://localhost:8000',
			'/audio': 'http://localhost:8000',
			'/config': 'http://localhost:8000',
			'/health': 'http://localhost:8000'
		}
	}
});
