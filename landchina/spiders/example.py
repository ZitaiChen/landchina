# -*- coding: utf-8 -*-
import scrapy
import json

class ExampleSpider(scrapy.Spider):
	name = 'example'
	allowed_domains = ["landchina.com"]
	start_urls = ["http://www.landchina.com/default.aspx?tabid=263&ComName=default"]

	def process_parameter(self,default=False):
		'''Three kinds of input parameter
			1. Variables: -a date = "2019-01-01~" ...
			2. Dictionary(str): -a conditions = \{'"key1":"value1","key2":"value2"'\}
			3. Json(filename): -a filename = "condition.json"
		'''
		conditions = {}

		if default:
			conditions['date'] = '2018-12-01~2019-01-01'
			conditions['district'] = '4401' + '广州市'
			conditions['use'] = '103'  + '街巷用地'
			conditions['supply'] = '1'  + '划拨'
			conditions['SortByTime'] = False
			print('Default settings are: ',conditions)
			return (conditions)

		filename = getattr(self, 'filename', None)
		if filename:
			'''Init the file to read'''
			# conditions['date'] = '2018-12-01~2019-01-01'
			# conditions['district'] = '4401' + '广州市'
			# with open(filename,'w', encoding = 'utf-8') as fileobject:
			# 	json.dump(conditions,fileobject,sort_keys=True, ensure_ascii=False, indent=4, separators=(',', ': '))

			with open(filename,'r', encoding = 'utf-8') as load_f:
				conditions = json.load(load_f)
				print('The input conditions are: ', conditions)
			return (conditions)

		inputs = getattr(self, 'conditions', None)
		if inputs:
			if isinstance(inputs,str):
				print('The input is a string')
				conditions = eval(inputs)
				print('The input conditions are: ', conditions)
			else:
				print('The input is error')
			return (conditions)

		if (inputs is None) and (filename is None):
			for item in ['date','district','use','supply','idnumber','location','area','sort','SortByTime']:
				data = getattr(self, item, None)
				if data:
					conditions[item] = data
			print('The input conditions are: ', conditions)
			return (conditions)

	def parse(self, response):
		print(response.url)
		conditions = self.process_parameter()


