# SSL bug with old sites
# https://github.com/psf/requests/issues/4775#issuecomment-478198879

import requests
import ssl
from urllib3 import poolmanager
import re

class TLSAdapter(requests.adapters.HTTPAdapter):
    def init_poolmanager(self, connections, maxsize, block=False):
        """Create and initialize the urllib3 PoolManager."""
        ctx = ssl.create_default_context()
        ctx.set_ciphers('DEFAULT@SECLEVEL=1')
        self.poolmanager = poolmanager.PoolManager(
                num_pools=connections,
                maxsize=maxsize,
                block=block,
                ssl_version=ssl.PROTOCOL_TLS,
                ssl_context=ctx)

s = requests.session()
s.mount('https://', TLSAdapter())

def get_javax_faces_ViewState(html):
	return re.findall('<input type="hidden" name="javax.faces.ViewState" id="javax.faces.ViewState" value="(.*?)" />', html)[0]

def login(card_number, registration):
	# Clear old cookies
	s.cookies.clear()

	# Get cookies/params
	r = s.get("https://si3.ufc.br/public/jsp/restaurante_universitario/consulta_comensal_ru.jsf")
	
	jfv = get_javax_faces_ViewState(r.text)
	JSESSIONID = r.cookies.get("JSESSIONID")

	# Login
	body = {
		"form": "form",
		"form:j_id_jsp_1091681061_2": card_number,
		"form:j_id_jsp_1091681061_3": registration,
		"form:j_id_jsp_1091681061_4": "Consultar",
		"javax.faces.ViewState": jfv,
	}

	r = s.post(f"https://si3.ufc.br/public/jsp/restaurante_universitario/consulta_comensal_ru.jsf;jsessionid={JSESSIONID}", data=body)

	jfv = get_javax_faces_ViewState(r.text)

	return jfv, JSESSIONID

def generate_gru(amount_credits, card_number, registration):
	# Generate pre-request
	jfv, JSESSIONID = login(card_number, registration)

	body = {
		# "AJAXREQUEST": "j_id_jsp_540432864_0",
		"form": "form",
		"form:qtdCreditos": amount_credits,
		"javax.faces.ViewState": jfv,
		# "form:j_id_jsp_540432864_3": "form:j_id_jsp_540432864_3",
	}

	r = s.post(f"https://si3.ufc.br/public/jsp/restaurante_universitario/gera_gru_restaurante.jsf", data=body)

	# Get generated GRU
	body = {
		"modalForm": "modalForm",
		"modalForm:btConfirmarGeracao": "Estou ciente",
		"javax.faces.ViewState": jfv,
	}

	r = s.post(f"https://si3.ufc.br/public/jsp/restaurante_universitario/gera_gru_restaurante.jsf", data=body)

	return r.content

def generate_pix(amount_credits, card_number, registration):
	# Generate pre-request
	jfv, JSESSIONID = login(card_number, registration)

	body = {
		# "AJAXREQUEST": "j_id_jsp_540432864_0",
		"form": "form",
		"form:qtdCreditos": amount_credits,
		"javax.faces.ViewState": jfv,
		# "form:j_id_jsp_540432864_3": "form:j_id_jsp_540432864_3",
	}

	r = s.post(f"https://si3.ufc.br/public/jsp/restaurante_universitario/gera_gru_restaurante.jsf", data=body)

	jfv = get_javax_faces_ViewState(r.text)

	# Get idSessao from generated PagTesouro page
	body = {
		"modalForm2": "modalForm2",
		"modalForm2:btConfirmarPagtesouro": "Estou ciente",
		"javax.faces.ViewState": jfv,
	}

	r = s.post(f"https://si3.ufc.br/public/jsp/restaurante_universitario/gera_gru_restaurante.jsf", data=body)

	idSessao = r.text.split('https://pagtesouro.tesouro.gov.br/#/pagamento?idSessao=')[1].split('&tema=')[0]

	# Send idSessao to dados-pagamento
	r = s.get(f"https://pagtesouro.tesouro.gov.br/api/pagamentos/dados-pagamento?idSessao={idSessao}")
	payment_details = r.json()

	# Get PIX info
	body = {
		"idSessao": idSessao,
		"informacoesAdicionais": [
			{
				"nome": "Origem",
				"valor": "PagTesouro"
			},
			{
				"nome": "Serviço",
				"valor": "6605 - Pagamento de taxa por utilização do RU"
			}
		]
	}

	r = s.post("https://pagtesouro.tesouro.gov.br/api/pagamentos/meios-pagamento/pix", json=body)
	pix_details = r.json()

	response = {
		"payment_details": payment_details,
		"pix_details": pix_details,
		"id_sessao": idSessao,
	}

	return response