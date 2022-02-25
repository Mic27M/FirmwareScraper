import pytest

from firmware.spiders import linksys
from firmware.tests.mock_classes import MockRequest, MockResponse

PRODUCT_LIST_PAGE = '''<!DOCTYPE html>
                        <html>
                            <head></head>
                            <body>
                                <main>
                                    <div>
                                        <div class="item">
                                            <ul>
                                                <li>
                                                    <a href="/de/support-product?pid=1234">Broadband Router</a>
                                                    <a href="/de/support-product?pid=5678">Modem Router</a>
                                                </li>
                                            </ul>
                                        </div>
                                    </div>
                                </main>
                            </body>
                        </html>
                     '''

PRODUCT_PAGE = '''<!DOCTYPE html>
                   <html>
                       <head></head>
                       <body>
                           <main>
                               <div>
                                   <div class="support-downloads col-sm-6">
                                       <div>
                                           <p>
                                               <a href="/de/support-article?articleNum=1234" title="Software Herunterladen">Software Herunterladen</a>
                                               <a href="/de/support-article?articleNum=4321" title="Lizensvereinbarung">Lizensvereinbarung</a>
                                           </p>
                                       </div>
                                   </div>
                               </div>
                           </main>
                       </body>
                   </html>
                 '''

FIRMWARE_PAGE = '''<!DOCTYPE html>
                    <html>
                        <head></head>
                        <body>
                            <div>
                                <div id="support-article-downloads">
                                    <div class="article-accordian-content collapse-me">
                                        <h3>Firmware (für USA)</h3>
                                        Ver.1.203.23 (build 20394)
                                        <br>
                                        Datum der letzten Version: 08/23/2019
                                        <br>
                                        <a href="http://downloads.linksys.com/downloads/firmware/FW_EA6300_1.203.23.20394_prod.gpg.img">Herunterladen</a>
                                        <a href="/de/support-article?articleNum=4321" title="Lizensvereinbarung">Lizensvereinbarung</a>
                                        <h3>Firmware (für andere Regionen)</h3>
                                        <p>
                                            Ver.2.03.21
                                            <br>
                                            Datum der letzten Version:
                                            <span>
                                                02/05/2018
                                                <br>
                                                <a href="http://downloads.linksys.com/downloads/firmware/FW_EA6300_2.03.21_prod.img">Herunterladen</a>
                                            </span>
                                        </p>
                                        <h3>Firmware</h3>
                                        Ver.2.03.21<br>
                                        Datum der letzten Version: 02/05/2018
                                        <br>
                                        <a href="http://downloads.linksys.com/downloads/firmware/FW_EA6300_2.03.21_prod.img">Herunterladen</a>
                                        <h3>Installation Tool</h3>
                                        Ver.1.1.0
                                        <br>
                                        Datum der letzten Version: 02/01/2018
                                        <br>
                                        <a href="http://downloads.linksys.com/downloads/firmware/FW_EA6300_2.03.21.exe">Herunterladen</a>
                                    </div>
                                </div>
                            </div>
                        </body>
                    </html>
                 '''

SEARCH_TEXT = '<h3>Firmware (für USA)</h3>Ver.1.203.23 (build 20394)<br>Datum der letzten Version: 08/23/2019<br>' \
              '<a href="http://downloads.linksys.com/downloads/firmware/FW_EA6300_1.203.23.20394_prod.gpg.img">' \
              'Herunterladen</a>'


@pytest.fixture(scope='session', autouse=True)
def spider_instance():
    return linksys.Linksys()


@pytest.fixture(scope='function', autouse=True)
def mocked_request(monkeypatch):
    monkeypatch.setattr(linksys, 'Request', MockRequest)


@pytest.fixture(scope='function', autouse=True)
def mock_parse():
    yield 1


@pytest.mark.parametrize('response, expected', [
    (MockResponse(url='https://www.linksys.com/de/support/sitemap/', body=PRODUCT_LIST_PAGE),
     [
         ('https://www.linksys.com/de/support-product?pid=1234', dict(device_name='Broadband Router')),
         ('https://www.linksys.com/de/support-product?pid=5678', dict(device_name='Modem Router'))
     ])
    ]
)
def test_parse(spider_instance, response, expected):
    for anchor, request in enumerate(list(spider_instance.parse(response=response))):
        assert request.url == expected[anchor][0]
        assert request.cb_kwargs == expected[anchor][1]


@pytest.mark.parametrize('response, device_name, expected', [
    (MockResponse(
        url='https://www.linksys.com/de/support-product?pid=1234',
        body=PRODUCT_PAGE
    ), 'Broadband Router', ('https://www.linksys.com/de/support-article?articleNum=1234', dict(device_name='Broadband Router'))
    )
    ]
)
def test_parse_product(spider_instance, response, device_name, expected):
    for request in spider_instance.parse_product(response=response, device_name=device_name):
        assert request.url == expected[0]
        assert request.cb_kwargs == expected[1]


@pytest.mark.parametrize('response, device_name, expected', [
    (MockResponse(
        url='https://www.linksys.com/de/support-article?articleNum=1234',
        body=FIRMWARE_PAGE
    ), 'Broadband Router', [1]
    )
    ]
)
def test_parse_versions(monkeypatch, spider_instance, response, device_name, expected):
    with monkeypatch.context() as monkey:
        monkey.setattr(linksys.Linksys, 'parse_urls', lambda *_, **__: [1])
        assert list(spider_instance.parse_versions(response=response, device_name=device_name)) == expected


@pytest.mark.parametrize('device_name, version, expected', [('WAG Broadband Router', FIRMWARE_PAGE, [1, 1, 1])])
def test_parse_urls(monkeypatch, spider_instance, device_name, version, expected):
    with monkeypatch.context() as monkey:
        monkey.setattr(linksys.Linksys, 'parse_firmware', lambda *_, **__: [1])
        assert list(spider_instance.parse_urls(device_name=device_name, version=version)) == expected


@pytest.mark.parametrize('meta_data, expected', [(dict(key=2), []), (dict(key3=3), [1])])
def test_parse_firmware(spider_instance, monkeypatch, meta_data, expected):
    with monkeypatch.context() as monkey:
        monkey.setattr(linksys.Linksys, 'prepare_item_pipeline', lambda *_, **__: [1])
        spider_instance.PRODUCT_DICTIONARIES = [dict(key=1), dict(key=2)]
        assert list(spider_instance.parse_firmware(meta_data=meta_data)) == expected


@pytest.mark.parametrize('meta_data, expected', [
    (dict(
        file_urls='http://downloads.linksys.com/downloads/firmware/FW_EA6300_1.203.23.20394_prod.gpg.img',
        vendor='Linksys',
        device_name='EA6300',
        firmware_version='1.203.23',
        device_class='Router',
        release_date='23-08-2019'
     ),
     dict(
         file_urls=['http://downloads.linksys.com/downloads/firmware/FW_EA6300_1.203.23.20394_prod.gpg.img'],
         vendor=['Linksys'],
         device_name=['EA6300'],
         firmware_version=['1.203.23'],
         device_class=['Router'],
         release_date=['23-08-2019']
     )
     )
   ]
)
def test_prepare_item_pipeline(spider_instance, meta_data, expected):
    assert list(spider_instance.prepare_item_pipeline(meta_data=meta_data))[0] == expected


@pytest.mark.parametrize('firmware, device_name, device_class, expected', [
    (SEARCH_TEXT, 'EA6300', 'Router',
     dict(
         file_urls='http://downloads.linksys.com/downloads/firmware/FW_EA6300_1.203.23.20394_prod.gpg.img',
         vendor='Linksys',
         device_name='EA6300',
         firmware_version='1.203.23',
         device_class='Router',
         release_date='2019-08-23'
     )
     )
    ]
)
def test_prepare_meta_data(spider_instance, firmware, device_name, device_class, expected):
    assert spider_instance.prepare_meta_data(firmware=firmware, device_name=device_name, device_class=device_class) == expected
