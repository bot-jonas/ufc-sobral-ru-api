import os
import json
from flask import Flask, request, make_response
import traceback as tb

from consulta_comensal import generate_gru, generate_pix

app = Flask(__name__)

@app.route('/gru.pdf', methods=['GET'])
def gru():
	amount_credits = request.args.get('amount_credits')
	card_number = request.args.get('card_number')
	registration = request.args.get('registration')

	data = generate_gru(amount_credits, card_number, registration)

	response = make_response(data)

	response.headers.set('Content-Type', 'application/pdf')
	# response.headers.set('Content-Disposition', 'attachment', filename='gru.pdf')
	response.headers.set("Cache-Control", "no-cache, no-store, must-revalidate")
	response.headers.set("Pragma", "no-cache")
	response.headers.set("Expires", "0")
	response.headers.set("Cache-Control", "public, max-age=0")

	return response

@app.route('/pix', methods=['POST'])
def pix():
	inp = request.get_json(force=True)

	try:
		amount_credits = inp["amount_credits"]
		card_number = inp["card_number"]
		registration = inp["registration"]
	except:
		return {
			"ok": False,
			"errors": [
				"Todos os parâmetros (amount_credits, card_number, registration) são necessários!",
			],
		}, 400

	try:
		data = generate_pix(amount_credits, card_number, registration)
	except:
		print(tb.format_exc())
		return {
			"ok": False,
			"errors": [
				"Não foi possível gerar o PIX!",
			],
		}, 500

	response = make_response({"ok": True, "data": data,})
	response.headers.set('Content-Type', 'application/json')

	return response

@app.route('/privacy', methods=['GET'])
def privacy():
	# Endpoint for Google Play Store
	return "Nenhum dado fornecido diretamente pelo o usuário é salvo. Entretanto, o aplicativo utiliza o CodePush para fazer certas atualizações sem passar pela Google Play Store, e esta biblioteca coleta alguns dados para fazer análises."

@app.route('/hello', methods=['GET'])
def hello():
	return "Hello World!"

if __name__ == "__main__":
	port = int(os.environ.get("PORT"))
	app.run(host='0.0.0.0', port=port)