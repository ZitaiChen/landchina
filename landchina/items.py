# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class TutorialItem(scrapy.Item):
	# define the fields for your item here like:
	# name = scrapy.Field()
	pass

class DmozItem(scrapy.Item):
	title = scrapy.Field()
	link  = scrapy.Field()
	desc  = scrapy.Field()

class LandChinaTableItem(scrapy.Item):
	serial_number = scrapy.Field() # 序号
	district      = scrapy.Field() # 行政区
	location      = scrapy.Field() # 土地坐落
	link          = scrapy.Field() # 网页连接
	area          = scrapy.Field() #总面积
	use           = scrapy.Field() # 土地用途
	supply        = scrapy.Field() # 供应方式
	date          = scrapy.Field() # 签订日期

class LandChinaItem(scrapy.Item):
	header                    = scrapy.Field() # 表头
	district                  = scrapy.Field() # 行政区
	idnumber                  = scrapy.Field() # 电子监管号
	name                      = scrapy.Field() # 项目名称
	location                  = scrapy.Field() # 项目位置
	area                      = scrapy.Field() # 面积（公顷）
	source                    = scrapy.Field() # 土地来源
	use                       = scrapy.Field() # 土地用途
	supply                    = scrapy.Field() # 供地方式
	duration                  = scrapy.Field() # 土地使用年限
	industry                  = scrapy.Field() # 行业分类
	grade                     = scrapy.Field() # 土地级别
	price                     = scrapy.Field() # 成交价格（万元）
	paid_plan                 = scrapy.Field() # 分期支付约定 [支付期号，约定支付日期，约定支付金额，备注]
	holder                    = scrapy.Field() # 土地使用权人
	plot_ratio_minimum        = scrapy.Field() # 容积率下限
	plot_ratio_maximum        = scrapy.Field() # 容积率上限
	time4handover_plan        = scrapy.Field() # 约定交地时间
	time4commencement_plan    = scrapy.Field() # 约定开工时间
	time4completion_plan      = scrapy.Field() # 约定竣工时间
	time4commencement_reality = scrapy.Field() # 实际开工时间
	time4completion_reality   = scrapy.Field() # 实际竣工时间
	approvedby                = scrapy.Field() # 批准单位
	date4sign                 = scrapy.Field() # 合同签订日期
	url                       = scrapy.Field() # 网址