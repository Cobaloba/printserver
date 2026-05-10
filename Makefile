PI_HOST = conor@192.168.0.25
PI_KEY  = ~/.ssh/pi_printserver

.PHONY: test redeploy

test:
	pytest backend/
	cd frontend && npm run test

redeploy:
	ssh -i $(PI_KEY) $(PI_HOST) 'cd ~/printserver && git pull && docker compose up --build -d'
