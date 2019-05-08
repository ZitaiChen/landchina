# !landchina_spider.py
# -*- coding: utf-8 -*-

import scrapy
import re
import json
from urllib.parse import unquote

from tutorial.items import LandChinaTableItem
from tutorial.items import LandChinaItem

'''
##### ##### ##### ##### ##### ##### ##### ##### ##### ##### 
The Request Procedure:
<-HTTP Request: GET: http://www.landchina.com/default.aspx?tabid=263&ComName=default
->HTTP Response + Set-Cookie: yunsuo_session_verify=...; expires=...; path=/; HttpOnly
<-HTTP Request + Cookie: GET: http://www.landchina.com/default.aspx?tabid=263&ComName=default&security_verify_data=313434302c393030, Cookie: yunsuo_session_verify=...; srcurl=...
->HTTP Response + Set-Cookie: security_session_mid_verify=...; expires=...; path=/; HttpOnly
<-HTTP Request + Cookie: GET: http://www.landchina.com/default.aspx?tabid=263&ComName=default, Cookie: yunsuo_session_verify=...; srcurl=...; security_session_mid_verify=...
->HTTP Response + Set-Cookie: ASP.NET_SessionId=...; path=/; HttpOnly
The last Response offers the desired information.
##### ##### ##### ##### ##### ##### ##### ##### ##### ##### 
Mind Map
Since acquiring cookies is a little bit cumbersome, we just copy the key one in file 'cookie.json'.
To fully parallelize the crawler, we first parallelize different conditions and request the first page only for it in FUNCTION start_requests().
After getting the first page with specific condition, we concurrently request all the record pages in FUNCTION next_page().
FUNCTION parse_page is called to save the records in different pages.
##### ##### ##### ##### ##### ##### ##### ##### ##### ##### 
start_requests(self): 
	Redefine the start function to POST different search condition parallely at the beginning.
	Only the first page of each condition is contained in this POST.
	The response is parsed by next_page().
	It is for paralleling conditions and getting the number of total pages under the specific condition.
process_parameter(self, default=False):
	It receive 3 kinds of parameter from command line: (Key:Value),(dictionary,str) and (filename).
process_input(self,conditions,item):
	It transform the input search condition to POST-ready format.
process_checkbox(self,response=None):
	It crawls the checkbox value from the response.html or uses the default one.
init_postdata(self,response=None):
	It initials the POST Formdata for this page.
parse_conditions_table(self,response=None):
	Crawl information from the search condition table
next_page(self, response):
	It parses the first page from the response under some specific conditions and POST pages.
	Crawl the POST conditions by parse_conditions_table():
	And then POST page-by-page from 1 to total_page.
	The response is parsed by parse_page().
parse_page(self, response):
	It crawls the table record and:
		* Stores the record only.
		Or
		* Follows the record link to GET the record details. 
		  The response is parsed by parse_item_link().
parse_item_link(self, response):
	It parses the record details and stores them.
'''


_sep = unquote('%A8%88', encoding='gbk')

class LandChinaPostSpider(scrapy.Spider):
	name = "landchinaV3"

	# Redefine Function start_requests()
	def start_requests(self):

		url = "http://www.landchina.com/default.aspx?tabid=263&ComName=default"
		print('URL: ',url)

		'''Initialing POST Form Data'''
		data=[]
		postdata = self.init_postdata()
		checkbox = self.process_checkbox()
		
		'''Parse Input Condition'''
		print('Processing the input conditions ......')
		conditions = self.process_parameter()

		'''Process different conditions to get parallel''' # FLAG
		for item in ['date','district','use','supply','idnumber','location','area']:
			if item in conditions.keys() and conditions[item]:
				if 'TAB_QueryConditionItem' not in postdata.keys() or not postdata['TAB_QueryConditionItem']:
					postdata['TAB_QueryConditionItem'] = checkbox[item]
				conditions = self.process_input(conditions=conditions, item=item)
				postdata['TAB_QuerySubmitConditionData'] = postdata['TAB_QuerySubmitConditionData'] + checkbox[item]+':'+conditions[item]+'|'
		postdata['TAB_QuerySubmitConditionData'] = postdata['TAB_QuerySubmitConditionData'][:-1] # delete the last "|"
		
		if 'SortByTime' in conditions.keys() and conditions['SortByTime']: # Sort by time
			checkbox['sort'] = "b42f6ce1-d810-4548-9581-725c9a501fc5:False" # response.xpath('//input[@id="TAB_QuerySort1"]').xpath('@value').extract()[0]
		postdata['TAB_QuerySortItemList'] = checkbox['sort'] # SortByDate by default
		postdata['TAB_QuerySubmitOrderData'] = postdata['TAB_QuerySortItemList']

		'''Post the first page only'''
		print('Posing parallel conditions in Page 1')
		postdata['TAB_QuerySubmitPagerData'] = '1'

		data.append(postdata)

		''' There is a verification at the first visit. 
		***CUSTOMIZED*** Copy the cookie value in users browser'''
		cookie = {}
		with open(cookie.json,'r', encoding = 'utf-8') as load_f:
			cookie = json.load(load_f)
			print('The cookie are: ', conditions)


		'''TO GET THE TOTAL PAGES NUMBER UNDER SPECIFIC CONDITIONS ONLY'''
		for formdata in data:
			print('The Post Form Data:', formdata)
			yield scrapy.FormRequest(
				url = url, 
				formdata = formdata,
				callback = self.next_page,
				encoding = 'gbk',
				cookies = cookie
				)

		print('Finished paralleling conditions for LandChina Spider!')


	def process_parameter(self,default=False):
		'''
			Three kinds of input parameter in command line: 
			($ scrapy crawl landchinaV3 -o output.json -a ...)
			1. Variables: -a date = "2019-01-01~" ...
			2. Dictionary(str): -a conditions = \{'"key1":"value1","key2":"value2"'\}
			3. Json(filename): -a filename = "conditions.json"
		'''
		
		conditions = {}
		filename = getattr(self, 'filename', None)
		if filename:
			'''
				Init the file to be read.
				See which directory the file should be placed.
			'''
			# conditions['date'] = '2018-12-1~2019-1-1'
			# conditions['district'] = '广州市'
			# print(conditions)
			# with open(filename,'w', encoding = 'utf-8') as fileobject:
			# 	json.dump(conditions,fileobject,sort_keys=True, ensure_ascii=False, indent=4, separators=(',', ': '))

			with open(filename,'r', encoding = 'utf-8') as load_f:
				conditions = json.load(load_f)
				print('The input conditions are: ', conditions)
				if conditions:
					return (conditions)
				else:
					default = True

		inputs = getattr(self, 'conditions', None)
		if inputs:
			if isinstance(inputs,str):
				print('The input is a string')
				conditions = eval(inputs)
				print('The input conditions are: ', conditions)
				return (conditions)
			else:
				print('The input is error')
				default = True
			
		if (inputs is None) and (filename is None):
			for item in ['date','district','use','supply','idnumber','location','area','SortByDate','SortByTime']:
				data = getattr(self, item, None)
				if data:
					conditions[item] = data
			print('The input conditions are: ', conditions)
			if conditions:
				return (conditions)
			else:
				default = True

		if default:
			conditions['date']       = '2018-12-1~2019-1-1'
			conditions['district']   = '广州市' # Processed by self.process_input
			conditions['use']        = '其他普通商品住房用地' # Processed by self.process_input
			# conditions['supply']     = '划拨' # Processed by self.process_input
			conditions['SortByTime'] = False
			print('Default settings are: ',conditions)
			return (conditions)


	def process_input(self,conditions,item):
		if item in ['date','area']:
			pass
		elif item in ['district','use','supply']:
			'''
				Update District to formdata format:
				e.g. '广州市' -> '4401▓~广州市' 
			
				Update Use to formdata format:
				e.g. '公共设施用地' -> '086▓~公共设施用地' 
			
				Update Supply to formdata format:
				e.g. '划拨' -> '1▓~划拨' 
			'''
			with open('dict_'+item+'.json','r') as load_f:
				print('Loading file dict_%s.json' % item)
				load_dict = json.load(load_f)
			name = conditions[item] 
			conditions[item] = load_dict[name] + _sep + '~' + name 
		elif item in ['idnumber','location']:
			'''
				Update Idnumber to formdata format:
				e.g. '4401122018A00827' -> '▓4401122018A00827▓' 

				Update Location to formdata format:
				e.g. '知识城北片区' -> '▓知识城北片区▓' 
			'''
			conditions[item] = _sep + conditions[item] + _sep 

		return(conditions)


	def process_checkbox(self,response=None):
		checkbox = {}
		if response:
			checkbox['date']     = response.xpath('//input[@id="TAB_QueryConditionItem270"]').xpath('@value').extract()[0]
			checkbox['district'] = response.xpath('//input[@id="TAB_QueryConditionItem256"]').xpath('@value').extract()[0]
			checkbox['use']      = response.xpath('//input[@id="TAB_QueryConditionItem212"]').xpath('@value').extract()[0]
			checkbox['supply']   = response.xpath('//input[@id="TAB_QueryConditionItem215"]').xpath('@value').extract()[0]
			checkbox['idnumber'] = response.xpath('//input[@id="TAB_QueryConditionItem218"]').xpath('@value').extract()[0]
			checkbox['location'] = response.xpath('//input[@id="TAB_QueryConditionItem269"]').xpath('@value').extract()[0]
			checkbox['area']     = response.xpath('//input[@id="TAB_QueryConditionItem284"]').xpath('@value').extract()[0]
			checkbox['sort']     = response.xpath('//input[@id="TAB_QuerySort0"]').xpath('@value').extract()[0]
		else: # When no response page can use
			checkbox['date']     = "9f2c3acd-0256-4da2-a659-6949c4671a2a"
			checkbox['district'] = "42ad98ae-c46a-40aa-aacc-c0884036eeaf"
			checkbox['use']      = "ec9f9d83-914e-4c57-8c8d-2c57185e912a"
			checkbox['supply']   = "8fd0232c-aff0-45d1-a726-63fc4c3d8ea9"
			checkbox['idnumber'] = "20f50617-f7d0-4d6c-b0df-7c24fcc5eed6"
			checkbox['location'] = "566b2f6d-5ef5-4ccf-8683-53492916fd2f"
			checkbox['area']     = "df7c2cd2-7afc-4f50-b52c-3c7ac512f5a6"
			checkbox['sort']     = "282:False" # SortByTime by default
		print('Checkbox all set!')
		return (checkbox)


	def init_postdata(self,response=None):
		'''Initialize Post Data'''
		if response:
			postdata = {  
				'__VIEWSTATE'                 : response.xpath('//input[@id="__VIEWSTATE"]').xpath('@value').extract()[0], #
				'__EVENTVALIDATION'           : response.xpath('//input[@id="__EVENTVALIDATION"]').xpath('@value').extract()[0], #
				'hidComName'                  : 'default', # 
				'TAB_QueryConditionItem'      : '', # Condition Checkbox
				'TAB_QuerySortItemList'       : '', # Sort By Date or Time
				'TAB_QuerySubmitConditionData': '', # Condition dict(key = Checkbox: value = ConditionValue)
				'TAB_QuerySubmitOrderData'    : '', # Sort By Date or Time
				'TAB_RowButtonActionControl'  : '', # NULL
				'TAB_QuerySubmitPagerData'    : '1', # Page
				'TAB_QuerySubmitSortData'     : '', # NULL
			}
		else: # When no response page can use
			postdata = {  
				'__VIEWSTATE'                 : "/wEPDwUJNjkzNzgyNTU4D2QWAmYPZBYIZg9kFgICAQ9kFgJmDxYCHgdWaXNpYmxlaGQCAQ9kFgICAQ8WAh4Fc3R5bGUFIEJBQ0tHUk9VTkQtQ09MT1I6I2YzZjVmNztDT0xPUjo7ZAICD2QWAgIBD2QWAmYPZBYCZg9kFgJmD2QWBGYPZBYCZg9kFgJmD2QWAmYPZBYCZg9kFgJmDxYEHwEFIENPTE9SOiNEM0QzRDM7QkFDS0dST1VORC1DT0xPUjo7HwBoFgJmD2QWAgIBD2QWAmYPDxYCHgRUZXh0ZWRkAgEPZBYCZg9kFgJmD2QWAmYPZBYEZg9kFgJmDxYEHwEFhwFDT0xPUjojRDNEM0QzO0JBQ0tHUk9VTkQtQ09MT1I6O0JBQ0tHUk9VTkQtSU1BR0U6dXJsKGh0dHA6Ly93d3cubGFuZGNoaW5hLmNvbS9Vc2VyL2RlZmF1bHQvVXBsb2FkL3N5c0ZyYW1lSW1nL3hfdGRzY3dfc3lfamhnZ18wMDAuZ2lmKTseBmhlaWdodAUBMxYCZg9kFgICAQ9kFgJmDw8WAh8CZWRkAgIPZBYCZg9kFgJmD2QWAmYPZBYCZg9kFgJmD2QWAmYPZBYCAgEPZBYCZg8WBB8BBSBDT0xPUjojMDQyZjYyO0JBQ0tHUk9VTkQtQ09MT1I6Ox8AaBYCZg9kFgICAQ9kFgJmDw8WAh8CZWRkAgMPZBYCAgMPFgQeCWlubmVyaHRtbAX6BjxwIGFsaWduPSJjZW50ZXIiPjxzcGFuIHN0eWxlPSJmb250LXNpemU6IHgtc21hbGwiPiZuYnNwOzxiciAvPg0KJm5ic3A7PGEgdGFyZ2V0PSJfc2VsZiIgaHJlZj0iaHR0cDovL3d3dy5sYW5kY2hpbmEuY29tLyI+PGltZyBib3JkZXI9IjAiIGFsdD0iIiB3aWR0aD0iMjYwIiBoZWlnaHQ9IjYxIiBzcmM9Ii9Vc2VyL2RlZmF1bHQvVXBsb2FkL2Zjay9pbWFnZS90ZHNjd19sb2dlLnBuZyIgLz48L2E+Jm5ic3A7PGJyIC8+DQombmJzcDs8c3BhbiBzdHlsZT0iY29sb3I6ICNmZmZmZmYiPkNvcHlyaWdodCAyMDA4LTIwMTggRFJDbmV0LiBBbGwgUmlnaHRzIFJlc2VydmVkJm5ic3A7Jm5ic3A7Jm5ic3A7IDxzY3JpcHQgdHlwZT0idGV4dC9qYXZhc2NyaXB0Ij4NCnZhciBfYmRobVByb3RvY29sID0gKCgiaHR0cHM6IiA9PSBkb2N1bWVudC5sb2NhdGlvbi5wcm90b2NvbCkgPyAiIGh0dHBzOi8vIiA6ICIgaHR0cDovLyIpOw0KZG9jdW1lbnQud3JpdGUodW5lc2NhcGUoIiUzQ3NjcmlwdCBzcmM9JyIgKyBfYmRobVByb3RvY29sICsgImhtLmJhaWR1LmNvbS9oLmpzJTNGODM4NTM4NTljNzI0N2M1YjAzYjUyNzg5NDYyMmQzZmEnIHR5cGU9J3RleHQvamF2YXNjcmlwdCclM0UlM0Mvc2NyaXB0JTNFIikpOw0KPC9zY3JpcHQ+Jm5ic3A7PGJyIC8+DQrniYjmnYPmiYDmnIkmbmJzcDsg5Lit5Zu95Zyf5Zyw5biC5Zy6572RJm5ic3A7Jm5ic3A75oqA5pyv5pSv5oyBOua1meaxn+iHu+WWhOenkeaKgOiCoeS7veaciemZkOWFrOWPuCZuYnNwOzxiciAvPg0K5aSH5qGI5Y+3OiDkuqxJQ1DlpIcwOTA3NDk5MuWPtyDkuqzlhaznvZHlronlpIcxMTAxMDIwMDA2NjYoMikmbmJzcDs8YnIgLz4NCjwvc3Bhbj4mbmJzcDsmbmJzcDsmbmJzcDs8YnIgLz4NCiZuYnNwOzwvc3Bhbj48L3A+HwEFZEJBQ0tHUk9VTkQtSU1BR0U6dXJsKGh0dHA6Ly93d3cubGFuZGNoaW5hLmNvbS9Vc2VyL2RlZmF1bHQvVXBsb2FkL3N5c0ZyYW1lSW1nL3hfdGRzY3cyMDEzX3l3XzEuanBnKTtkZH/OVsj/tQERwnER2qKWinV4FTmpxtgEKfV5ZGxVBl4Y", #
				'__EVENTVALIDATION'           : "/wEWAgKaycjzCgLN3cj/BKermgbYE2xpIYYf9ceNcxy5/OUYiJOhufs3lFPSBKIc", #
				'hidComName'                  : 'default', # 
				'TAB_QueryConditionItem'      : '', # Condition Checkbox
				'TAB_QuerySortItemList'       : '', # Sort By Date or Time
				'TAB_QuerySubmitConditionData': '', # Condition dict(key = Checkbox: value = ConditionValue)
				'TAB_QuerySubmitOrderData'    : '', # Sort By Date or Time
				'TAB_RowButtonActionControl'  : '', # NULL
				'TAB_QuerySubmitPagerData'    : '1', # Page
				'TAB_QuerySubmitSortData'     : '', # NULL
			}
		return (postdata)


	def parse_conditions_table(self,response=None):
		'''
			Crawl information from the search condition table
		'''
		conditions = {}
		if not response:
			pass
		else:
			'''Find out the checked search conditions'''
			checked = response.xpath('//input[@checked="checked"]').xpath('@id').extract() # ['TAB_QueryConditionItem270', 'TAB_QueryConditionItem256', 'TAB_QueryConditionItem212', 'TAB_QueryConditionItem215', 'TAB_QuerySort0']

			if 'TAB_QueryConditionItem270' in checked: # Date
				begin = response.xpath('//input[@id="TAB_queryDateItem_270_1"]').xpath('@value').extract()
				begin = begin[0] if begin else ''
				end = response.xpath('//input[@id="TAB_queryDateItem_270_2"]').xpath('@value').extract()
				end = end[0] if end else ''
				conditions['date'] = begin + '~' + end
			if 'TAB_QueryConditionItem256' in checked: # District
				name = response.xpath('//*[@id="TAB_queryTblEnumItem_256"]').xpath('@value').extract()[0]
				code = response.xpath('//*[@id="TAB_queryTblEnumItem_256_v"]').xpath('@value').extract()[0]
				conditions['district'] = code + '~' + name
			if 'TAB_QueryConditionItem212' in checked: # Use
				name = response.xpath('//*[@id="TAB_queryTblEnumItem_212"]').xpath('@value').extract()[0]
				code = response.xpath('//*[@id="TAB_queryTblEnumItem_212_v"]').xpath('@value').extract()[0]
				conditions['use'] = code + '~' + name
			if 'TAB_QueryConditionItem215' in checked: # Supply
				name = response.xpath('//*[@id="TAB_queryTblEnumItem_215"]').xpath('@value').extract()[0]
				code = response.xpath('//*[@id="TAB_queryTblEnumItem_215_v"]').xpath('@value').extract()[0]
				conditions['supply'] = code + '~' + name
			if 'TAB_QueryConditionItem218' in checked: # Idnumber
				conditions['idnumber'] = _sep + response.xpath('//*[@id="TAB_queryTextItem_218"]').xpath('@value').extract()[0] + _sep
			if 'TAB_QueryConditionItem269' in checked: # Location
				conditions['location'] = _sep + response.xpath('//*[@id="TAB_queryTextItem_269"]').xpath('@value').extract()[0] + _sep
			if 'TAB_QueryConditionItem284' in checked: # Area
				symbol = response.xpath('//*[@id="TAB_queryOpItem_284"]/option[1]').xpath('@value').extract()[0]
				number = response.xpath('//*[@id="TAB_queryNumberItem_284"]').xpath('@value').extract()[0]
				conditions['area'] = symbol + number
			if 'TAB_QuerySort1' in checked: # SortByTime
				conditions['sort'] = 'SortByTime'

		return conditions


	def next_page(self, response):
		'''Get a post response'''
		print('Get the POST response page successfully!')

		filename = response.url.split("/")[-2] + '.html'
		with open(filename, 'wb') as f:
			f.write(response.body)
		print('Finishing saving the page')
		
		data = self.init_postdata(response = response)
		checkbox = self.process_checkbox(response = response)

		''' Crawl information from the conditions table for next-page POST which is POST-ready conditions '''
		conditions = self.parse_conditions_table(response = response)

		'''Process different conditions'''
		for item in ['date','district','use','supply','idnumber','location','area']:
			if item in conditions.keys() and conditions[item]: # The dictionary key exists and not empty
				if 'TAB_QueryConditionItem' not in data.keys() or not data['TAB_QueryConditionItem']:
					data['TAB_QueryConditionItem'] = checkbox[item]
				data['TAB_QuerySubmitConditionData'] = data['TAB_QuerySubmitConditionData'] + checkbox[item]+':'+conditions[item]+'|'
		data['TAB_QuerySubmitConditionData'] = data['TAB_QuerySubmitConditionData'][:-1] # delete the last "|"
		
		if 'SortByTime' in conditions.keys() and conditions['SortByTime']: # Sort by time
			checkbox['sort'] = response.xpath('//input[@id="TAB_QuerySort1"]').xpath('@value').extract()[0]
		data['TAB_QuerySortItemList'] = checkbox['sort'] # SortByDate by default
		data['TAB_QuerySubmitOrderData'] = data['TAB_QuerySortItemList']


		'''TO GET THE TOTAL PAGES NUMBER UNDER SPECIFIC CONDITIONS ONLY'''
		total_page = int(re.search('共([0-9]*)页', response.text).group(1)) if re.search('共([0-9]*)页', response.text) else 1
		print('Total Page: %s' % str(total_page))
		if total_page > 200 : # FLAG: SOME SOLUTION MIGHT BE NEEDED
			print('There are %s pages exist, but we can only crawl 200 pages' % str(total_page))
			total_page = 200

		print('Posing SPECIFIC conditions Page-by-Page')
		page = 1
		while page <= total_page:
			data['TAB_QuerySubmitPagerData'] = str(page)
			print('Posting Page ',page)
			yield scrapy.FormRequest(
				url = response.url, 
				formdata = data,
				callback = self.parse_page,
				encoding = 'gbk'
				)
			page += 1

		print('Finished Crawler!')


	def parse_page(self, response):
		filename = response.url.split("/")[-2] + '.html'
		with open(filename, 'wb') as f:
			f.write(response.body)
		print('Finishing saving the page')
		print('Processing items in the page.')
		'''Process the list'''
		for sel in response.xpath('//table[@id="TAB_contentTable"]//tr[@onmouseover]'):
			item = LandChinaTableItem()
			try:
				item['serial_number'] = sel.css('.gridTdNumber::text').extract()[0]
			except Exception as e:
				item['serial_number'] = ''
			try:
				# item['location'] = sel.xpath('td/a//@title').extract()[0].encode('gbk') if sel.xpath('td/a//@title').extract() else sel.xpath('td/a//text()').extract()[0].encode('gbk')
				item['location'] = sel.xpath('td/a//@title').extract()[0] if sel.xpath('td/a//@title').extract() else sel.xpath('td/a//text()').extract()[0]
			except Exception as e:
				item['location'] = ''
			try:
				item['link'] = 'http://www.landchina.com/' + sel.xpath('td/a/@href').extract()[0]
			except Exception as e:
				item['link'] = ''
			try:
				[item['district'], item['area'], item['use'], item['supply'], item['date']] = sel.css('.queryCellBordy::text').extract()
			except Exception as e:
				[item['district'], item['area'], item['use'], item['supply'], item['date']] = ['','','','','']
			print(item['serial_number'],item['location'],item['link'],item['district'], item['area'], item['use'], item['supply'], item['date'])
			
			'''Store the record only '''
			yield item

			'''Follow links in the list and GET record details '''
			# url = item['link']
			# yield scrapy.Request(url, callback=self.parse_item_link)


	def parse_item_link(self, response):

		# is there table exist ?
		sel = response.xpath('//table[@id="mainModuleContainer_1855_1856_ctl00_ctl00_p1_f1"]')
		if not sel: 
			print(response.url) # print to file to re-crawl this link for now
			return

		item = LandChinaItem()
		item['url'] = response.url

		try:
			item['header'] = sel.xpath(
				'//span[@id="mainModuleContainer_1855_1856_ctl00_ctl00_p1_f1_r8_c1_ctrl"]/text()').extract()[0] # 表头
		except Exception as e:
			item['header'] = ''
		try:
			item['district'] = sel.xpath(
				'//span[@id="mainModuleContainer_1855_1856_ctl00_ctl00_p1_f1_r1_c2_ctrl"]/text()').extract()[0] # 行政区
		except Exception as e:
			item['district'] = ''
		try:
			item['idnumber'] = sel.xpath(
				'//span[@id="mainModuleContainer_1855_1856_ctl00_ctl00_p1_f1_r1_c4_ctrl"]/text()').extract()[0] # 电子监管号
		except Exception as e:
			item['idnumber'] = ''
		try:
			item['name'] = sel.xpath(
				'//span[@id="mainModuleContainer_1855_1856_ctl00_ctl00_p1_f1_r17_c2_ctrl"]/text()').extract()[0] # 项目名称
		except Exception as e:
			item['name'] = ''
		try:
			item['location'] = sel.xpath(
				'//span[@id="mainModuleContainer_1855_1856_ctl00_ctl00_p1_f1_r16_c2_ctrl"]/text()').extract()[0] # 项目位置
		except Exception as e:
			item['location'] = ''
		try:
			item['area'] = sel.xpath(
				'//span[@id="mainModuleContainer_1855_1856_ctl00_ctl00_p1_f1_r2_c2_ctrl"]/text()').extract()[0] # 面积（公顷）
		except Exception as e:
			item['area'] = ''
		try:
			source = sel.xpath(
				'//span[@id="mainModuleContainer_1855_1856_ctl00_ctl00_p1_f1_r2_c4_ctrl"]/text()').extract()[0] # 土地来源
			if item['area'] == source: # should be placed in file pipelines.py
				item['source'] = "现有建设用地"
			elif source == 0:
				item['source'] = "新增建设用地"
			else:
				item['source'] = "新增建设用地(来自存量库)"
		except Exception as e:
			item['source'] = ''
		try:
			item['use'] = sel.xpath(
				'//span[@id="mainModuleContainer_1855_1856_ctl00_ctl00_p1_f1_r3_c2_ctrl"]/text()').extract()[0] # 土地用途
		except Exception as e:
			item['use'] = ''
		try:
			item['supply'] = sel.xpath(
				'//span[@id="mainModuleContainer_1855_1856_ctl00_ctl00_p1_f1_r3_c4_ctrl"]/text()').extract()[0] # 供地方式
		except Exception as e:
			item['supply'] = ''
		try:
			item['duration'] = sel.xpath(
				'//span[@id="mainModuleContainer_1855_1856_ctl00_ctl00_p1_f1_r19_c2_ctrl"]/text()').extract()[0] # 土地使用年限
		except Exception as e:
			item['duration'] = ''
		try:
			item['industry'] = sel.xpath(
				'//span[@id="mainModuleContainer_1855_1856_ctl00_ctl00_p1_f1_r19_c4_ctrl"]/text()').extract()[0] # 行业分类
		except Exception as e:
			item['industry'] = ''
		try:
			item['grade'] = sel.xpath(
				'//span[@id="mainModuleContainer_1855_1856_ctl00_ctl00_p1_f1_r20_c2_ctrl"]/text()').extract()[0] # 土地级别
		except Exception as e:
			item['grade'] = ''
		try:
			item['price'] = sel.xpath(
				'//span[@id="mainModuleContainer_1855_1856_ctl00_ctl00_p1_f1_r20_c4_ctrl"]/text()').extract()[0] # 成交价格（万元）
		except Exception as e:
			item['price'] = ''
		try:
			for rec in sel.xpath('//tr[@kvalue]'):
				term = rec.xpath('td/span/text()').extract()
				item['paid_plan'] = {term[0]: term[1:]} # 分期支付约定 [支付期号，约定支付日期，约定支付金额，备注]
		except Exception as e:
			item['paid_plan'] = ''
		try:
			item['holder'] = sel.xpath(
				'//span[@id="mainModuleContainer_1855_1856_ctl00_ctl00_p1_f1_r9_c2_ctrl"]/text()').extract()[0] # 土地使用权人
		except Exception as e:
			item['holder'] = ''
		try:
			item['plot_ratio_minimum'] = sel.xpath(
				'//span[@id="mainModuleContainer_1855_1856_ctl00_ctl00_p1_f2_r1_c2_ctrl"]/text()').extract()[0] # 容积率下限
		except Exception as e:
			item['plot_ratio_minimum'] = ''
		try:
			item['plot_ratio_maximum'] = sel.xpath(
				'//span[@id="mainModuleContainer_1855_1856_ctl00_ctl00_p1_f2_r1_c4_ctrl"]/text()').extract()[0] # 容积率上限
		except Exception as e:
			item['plot_ratio_maximum'] = ''
		try:
			item['time4handover_plan'] = sel.xpath(
				'//span[@id="mainModuleContainer_1855_1856_ctl00_ctl00_p1_f1_r21_c4_ctrl"]/text()').extract()[0] # 约定交地时间
			if item['time4handover_plan'] == "1900-01-01": # should be placed in file pipelines.py 
				item['time4handover_plan'] == ''
		except Exception as e:
			item['time4handover_plan'] = ''
		try:
			item['time4commencement_plan'] = sel.xpath(
				'//span[@id="mainModuleContainer_1855_1856_ctl00_ctl00_p1_f1_r22_c2_ctrl"]/text()').extract()[0] # 约定开工时间
			if item['time4commencement_plan'] == "1900-01-01": # should be placed in file pipelines.py 
				item['time4commencement_plan'] == ''
		except Exception as e:
			item['time4commencement_plan'] = ''
		try:
			item['time4completion_plan'] = sel.xpath(
				'//span[@id="mainModuleContainer_1855_1856_ctl00_ctl00_p1_f1_r22_c4_ctrl"]/text()').extract()[0] # 约定竣工时间
			if item['time4completion_plan'] == "1900-01-01": # should be placed in file pipelines.py 
				item['time4completion_plan'] == ''
		except Exception as e:
			item['time4completion_plan'] = ''
		try:
			item['time4commencement_reality'] = sel.xpath(
				'//span[@id="mainModuleContainer_1855_1856_ctl00_ctl00_p1_f1_r10_c2_ctrl"]/text()').extract()[0] # 实际开工时间
			if item['time4commencement_reality'] == "1900-01-01": # should be placed in file pipelines.py 
				item['time4commencement_reality'] == ''
		except Exception as e:
			item['time4commencement_reality'] = ''
		try:
			item['time4completion_reality'] = sel.xpath(
				'//span[@id="mainModuleContainer_1855_1856_ctl00_ctl00_p1_f1_r10_c4_ctrl"]/text()').extract()[0].replace(u'\xa0', u' ') # 实际竣工时间
			if item['time4completion_reality'] == "1900-01-01": # should be placed in file pipelines.py 
				item['time4completion_reality'] == ''
		except Exception as e:
			item['time4completion_reality'] = ''
		try:
			item['approvedby'] = sel.xpath(
				'//span[@id="mainModuleContainer_1855_1856_ctl00_ctl00_p1_f1_r14_c2_ctrl"]/text()').extract()[0] # 批准单位
			if item['approvedby'] != '' and not re.search("人民政府",item['approvedby']): # should be placed in file pipelines.py 
				item['approvedby'] = item['approvedby'] + "人民政府"
		except Exception as e:
			item['approvedby'] = ''
		try:
			item['date4sign'] = sel.xpath(
				'//span[@id="mainModuleContainer_1855_1856_ctl00_ctl00_p1_f1_r14_c4_ctrl"]/text()').extract()[0] # 合同签订日期
		except Exception as e:
			item['date4sign'] = ''
		yield item




'''
scrapy crawl landchinapost -o output.json
'''

