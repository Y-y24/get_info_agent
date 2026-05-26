from unittest.mock import patch, Mock
from fetchers.academic import ArxivFetcher


ARXIV_XML_RESPONSE = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <title>Attention Is All You Need</title>
    <id>http://arxiv.org/abs/1706.03762v1</id>
    <summary>We propose a new simple network architecture...</summary>
    <author><name>Ashish Vaswani</name></author>
    <published>2017-06-12T17:57:34Z</published>
    <link href="http://arxiv.org/abs/1706.03762v1" rel="alternate"/>
  </entry>
  <entry>
    <title>BERT: Pre-training of Deep Bidirectional Transformers</title>
    <id>http://arxiv.org/abs/1810.04805v1</id>
    <summary>We introduce a new language representation model...</summary>
    <author><name>Jacob Devlin</name></author>
    <published>2018-10-11T17:57:34Z</published>
    <link href="http://arxiv.org/abs/1810.04805v1" rel="alternate"/>
  </entry>
</feed>"""


def test_arxiv_fetcher_parses_atom_xml():
    mock_resp = Mock()
    mock_resp.text = ARXIV_XML_RESPONSE
    mock_resp.raise_for_status = Mock()

    with patch("requests.get", return_value=mock_resp):
        items = ArxivFetcher(categories=["cs.AI"]).fetch()

    assert len(items) == 2
    assert items[0].title == "Attention Is All You Need"
    assert items[0].source == "arxiv"
    assert items[0].category == "academic"
    assert "arxiv.org/abs/1706.03762" in items[0].url


def test_arxiv_fetcher_builds_correct_query_url():
    fetcher = ArxivFetcher(categories=["cs.AI", "cs.CL"])
    url = fetcher._build_url()
    assert "cat%3Acs.AI" in url or "cat:cs.AI" in url
    assert "cat%3Acs.CL" in url or "cat:cs.CL" in url
    assert "sortBy=submittedDate" in url


def test_huggingface_fetcher_parses_html():
    html = """
    <html><body>
    <article class="flex flex-col">
      <a href="/papers/paper1">Paper Title One</a>
      <p>Abstract text for paper one about machine learning.</p>
    </article>
    <article class="flex flex-col">
      <a href="/papers/paper2">Paper Title Two</a>
      <p>Abstract text for paper two about NLP.</p>
    </article>
    </body></html>
    """
    mock_resp = Mock()
    mock_resp.text = html
    mock_resp.raise_for_status = Mock()

    from fetchers.academic import HuggingFaceFetcher

    with patch("requests.get", return_value=mock_resp):
        items = HuggingFaceFetcher().fetch()

    assert len(items) >= 2
    assert all(i.source == "huggingface" for i in items)
    assert all(i.category == "academic" for i in items)


def test_arxiv_fetcher_empty_response():
    empty_xml = """<?xml version="1.0"?>
    <feed xmlns="http://www.w3.org/2005/Atom">
    </feed>"""
    mock_resp = Mock()
    mock_resp.text = empty_xml
    mock_resp.raise_for_status = Mock()

    with patch("requests.get", return_value=mock_resp):
        items = ArxivFetcher(categories=["cs.AI"]).fetch()

    assert items == []
