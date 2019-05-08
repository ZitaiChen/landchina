# !landchina_spider.py
# -*- coding: utf-8 -*-

import scrapy
import re
from urllib.parse import unquote

from tutorial.items import LandChinaTableItem
from tutorial.items import LandChinaItem

_sep = unquote('%A8%88%7E', encoding='gbk')

class LandChinaPostSpider(scrapy.Spider):
	name = "landchinaV2"

	def start_requests(self):

		urls = [
			"http://www.landchina.com/default.aspx?tabid=263&ComName=default"
		]

		for url in urls:
			yield scrapy.Request(url=url, callback=self.parse)

	def parse(self, response):
		self.maxPage = 30

		'''Get a response'''
		print('Get the page successfully!')
		'''Initialize Post Data'''
		data = {  
			'__VIEWSTATE'                 : '', #
			'__EVENTVALIDATION'           : '', #
			'hidComName'                  : '', # 
			'TAB_QueryConditionItem'      : '', # Condition Checkbox
			'TAB_QuerySortItemList'       : '', # Sort By Date or Time
			'TAB_QuerySubmitConditionData': '', # Condition dict(key = Checkbox: value = ConditionValue)
			'TAB_QuerySubmitOrderData'    : '', # Sort By Date or Time
			'TAB_RowButtonActionControl'  : '', # NULL
			'TAB_QuerySubmitPagerData'    : '', # Page
			'TAB_QuerySubmitSortData'     : '', # NULL
		}

		'''Get Post Data'''
		data['__VIEWSTATE'] = response.xpath('//input[@id="__VIEWSTATE"]').xpath('@value').extract()[0]
		data['__EVENTVALIDATION'] = response.xpath('//input[@id="__EVENTVALIDATION"]').xpath('@value').extract()[0]
		data['hidComName'] = 'default'
		

		checkbox = {}
		checkbox['date']     = response.xpath('//input[@id="TAB_QueryConditionItem270"]').xpath('@value').extract()[0]
		checkbox['district'] = response.xpath('//input[@id="TAB_QueryConditionItem256"]').xpath('@value').extract()[0]
		checkbox['use']      = response.xpath('//input[@id="TAB_QueryConditionItem212"]').xpath('@value').extract()[0]
		checkbox['supply']   = response.xpath('//input[@id="TAB_QueryConditionItem215"]').xpath('@value').extract()[0]
		checkbox['idnumber'] = response.xpath('//input[@id="TAB_QueryConditionItem218"]').xpath('@value').extract()[0]
		checkbox['location'] = response.xpath('//input[@id="TAB_QueryConditionItem269"]').xpath('@value').extract()[0]
		checkbox['area']     = response.xpath('//input[@id="TAB_QueryConditionItem284"]').xpath('@value').extract()[0]
		checkbox['sort']     = response.xpath('//input[@id="TAB_QuerySort0"]').xpath('@value').extract()[0]
		print('Checkbox all set!')

		'''Parse Input Condition'''
		input_condition = {}
		input_condition['date'] = '2018-12-01~2019-01-01'
		input_condition['district'] = '4401'+ _sep + '广州市'
		# input_condition['use'] = '103' + _sep + '街巷用地'
		# input_condition['supply'] = '1' + _sep + '划拨'
		input_condition['SortByTime'] = False

		data['TAB_QueryConditionItem'] = checkbox['date']
		data['TAB_QuerySubmitConditionData'] = data['TAB_QuerySubmitConditionData'] + checkbox['date']+':'+input_condition['date']+'|'
		data['TAB_QuerySubmitConditionData'] = data['TAB_QuerySubmitConditionData'] + checkbox['district']+':'+input_condition['district']+'|' # city: 4401▓~广州市 
		# data['TAB_QuerySubmitConditionData'] = data['TAB_QuerySubmitConditionData'] + checkbox['use']+':'+input_condition['use']+'|'
		# data['TAB_QuerySubmitConditionData'] = data['TAB_QuerySubmitConditionData'] + checkbox['supply']+':'+input_condition['supply']+'|'

		data['TAB_QuerySubmitConditionData'] = data['TAB_QuerySubmitConditionData'][:-1] # delete the last "|"
		
		if 'SortByTime' in input_condition.keys() and input_condition['SortByTime']: # Sort by time
			checkbox['sort'] = response.xpath('//input[@id="TAB_QuerySort1"]').xpath('@value').extract()[0]
			del input_condition['SortByTime']
		data['TAB_QuerySortItemList'] = checkbox['sort'] # SortByDate by default
		data['TAB_QuerySubmitOrderData'] = data['TAB_QuerySortItemList']
		
		'''Process'''
		self.maxPage = 5
		print('Processing start_urls')
		page = 1
		while page < self.maxPage:
			data['TAB_QuerySubmitPagerData'] = str(page)
			print('Page: ',page)


			if page > self.maxPage:
				break

			yield scrapy.FormRequest(
				url = response.url, 
				formdata = data,
				callback = self.parse_page,
				encoding = 'gbk'
				)
			page = page + 1
		print('Finished LandChina Spider!')

	def parse_page(self, response):
		filename = response.url.split("/")[-2] + '.html'
		with open(filename, 'wb') as f:
			f.write(response.body)
		print('Finishing saving the page')

		'''Process the list'''
		for sel in response.xpath('//table[@id="TAB_contentTable"]//tr[@onmouseover]'):
			item = LandChinaTableItem()
			try:
				item['serial_number'] = sel.css('.gridTdNumber::text').extract()[0]
			except Exception as e:
				item['serial_number'] = ''
			try:
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
			# yield item

			'''Process item link in the list'''
			url = item['link']
			yield scrapy.Request(url, callback=self.parse_item_link)
		
		totalpage = int(re.search('共([0-9]*)页', response.text).group(1))
		self.maxPage = totalpage
		
		print(type(totalpage))
		print('Total pages: ', totalpage)

		return totalpage


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


	
	# # Redefine function start_requests()
	# def start_requests(self):

	# 	# FormRequest 是Scrapy发送POST请求的方法
	# 	yield scrapy.FormRequest(
	# 		url = start_urls,
	# 		formdata = post_formdata,
	# 		callback = self.parse_page
	# 	)

		


'''
LANDCHINA_LIST
response.xpath('//table[@id="TAB_contentTable"]').extract()
response.xpath('//table[@id="TAB_contentTable"]//tr[@onmouseover]').extract()
<span id="mainModuleContainer_1855_1856_ctl00_ctl00_p1_f1_r10_c4_ctrl">&nbsp;</span>
LANDCHINA_TABLE

scrapy crawl landchinapost -o terms.json
'''

