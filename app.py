from flask import Flask, render_template, request
import requests
from bs4 import BeautifulSoup
import re


app = Flask(__name__)

@app.route('/')
def index():
	return render_template('index.html')

@app.route('/result', methods=['POST'])
def result():
	number = request.form['number']
	lawsuit = get_lawsuit(number)
	if not lawsuit:
		return render_template('notfound.html')

	return lawsuit

def get_lawsuit(number):
	print('fazendo requisicao do cabecalho do processo')

	lawsuits = []
	
	params = {
		#'conversationId':'',
		'cbPesquisa':'NUMPROC',
		#'numeroDigitoAnoUnificado':'',
		#'foroNumeroUnificado':'',
		'dadosConsulta.valorConsultaNuUnificado': number,
		#'dadosConsulta.valorConsulta':'',
		'dadosConsulta.tipoNuProcesso':'UNIFICADO',
		#'uuidCaptcha':''
	}

	# params2 = {
	# 	'conversationId':'',
	# 	#'paginaConsulta':'0',
	# 	'cbPesquisa':'NUMPROC',
	# 	#'numeroDigitoAnoUnificado':'0800-88.2021',
	# 	#'foroNumeroUnificado':'',
	# 	'dePesquisaNuUnificado': number,
	# 	#'dadosConsulta.valorConsulta':'',
	# 	'tipoNuProcesso':'UNIFICADO',
	# 	#'uuidCaptcha':''
	# }
	
	response_1degree = requests.get('https://www2.tjal.jus.br/cpopg/search.do',params=params)
	# response_2degree = requests.get('https://www2.tjal.jus.br/cposg5/search.do',params=params2)
	
	# for response in [response_1degree, response_2degree]:
	# 	lawsuit = parse(response.content)
	# 	if lawsuit:
	# 		lawsuits.append(lawsuit)
	# import pdb; pdb.set_trace()
	lawsuit = parse(response_1degree.content)
	return lawsuit
	# return lawsuits

def parse(data):
	print('filtrando as informacoes')

	parsed = BeautifulSoup(data,'html.parser')
	text = parsed.text
	if not_found(text):
		return
	subject = extract_by_regex(re.compile(r'Assunto:\s*(.*)'),text)
	number = get_number(text)
	class_ = extract_by_regex(re.compile(r'Classe:\s*(.*)'),text)
	distribution_date = extract_by_regex(re.compile(r'Distribui.*o:\s*(\d{2}/\d{2}/\d{2,4})'),text)
	judge = extract_by_regex(re.compile(r'Juiz:\s*(.*)'),text)
	value = extract_by_regex(re.compile(r'Valor da a.*o:\s*(.*)'),text)
	court_section = extract_by_regex(re.compile(r'(\d{1,2}.\sVara.*)'),text)
	related_people = get_related_people(parsed)
	activity_list = get_activity_list(parsed)


	lawsuit = {
		'subject':subject,
		'number':number,
		'class_':class_,
		'distribution_date':distribution_date,
		'judge':judge,
		'value':value,
		'court_section':court_section,
		'related_people':related_people,
		'activity_list':activity_list,
	}

	return lawsuit	

def not_found(text):

	result = re.search('N.*o existem infor', text)
	if result:
		return True


def extract_by_regex(regex,data):

	result = regex.search(data,re.IGNORECASE)
	if result:
		return result.group(1).strip()


def normalize_text(text):

	return text.replace('\n','').replace('\t','').strip()

def get_number(data):
	print('extraindo o numero do processo')

	result = re.search(r'\d{7}-\d{2}.\d{4}.\d.\d{2}.\d{4}',data)
	if result: 
		return result.group()

def get_related_people(data):
	print('extraindo partes do processo')

	related_people = []
	# import pdb; pdb.set_trace()
	table = data.find('table', id='tablePartesPrincipais')
	trs = table.find_all('tr')
	for tr in trs:
		person = {}
		tds = tr.find_all('td')
		if len(tds)>1:
			name = normalize_text(tds[1].text)
			person['role'] = normalize_text(tds[0].text)
			person['name'] = re.sub(r'Advoga.*','',name).strip()
			person['lawyer'] = re.search(r'Advogad.:(.*)',name).group(1).strip()
			related_people.append(person)

	return related_people

def get_activity_list(data):
	print('extraindo as movimentacoes do processo')
	
	activity_list = []
	tbody = data.find('tbody',id='tabelaTodasMovimentacoes')
	trs = tbody.find_all('tr')
	for tr in trs:
		tds = tr.find_all('td')
		activity = {
		'text':normalize_text(tds[2].text.strip()),
		'date':normalize_text(tds[0].text.strip())
		}
		activity_list.append(activity)
	
	return activity_list


# print(get_lawsuit("0701316-22.2020.8.02.0051"))




if __name__ == '__main__':
	app.run()	
