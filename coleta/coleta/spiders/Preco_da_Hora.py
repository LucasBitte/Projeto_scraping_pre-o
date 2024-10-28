import scrapy


class PrecoDaHoraSpider(scrapy.Spider):
    name = "Preco_da_Hora"
    allowed_domains = ["precodahora.ba.gov.br"]
    start_urls = ["https://precodahora.ba.gov.br/produtos/"]

    def parse(self, response):
        pass
