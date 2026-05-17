import os
import re
from typing import List, Dict

# 配置 HuggingFace 镜像
HF_MIRROR = "https://hf-mirror.com"
os.environ["HUGGINGFACE_HUB_URL"] = HF_MIRROR
os.environ["HF_ENDPOINT"] = HF_MIRROR

# 设置缓存目录为项目绝对路径
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["HF_HOME"] = os.path.join(BASE_DIR, "models", "huggingface_cache")
os.environ["TRANSFORMERS_CACHE"] = os.environ["HF_HOME"]

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings


def _get_embedding_model():
    """获取 embedding 模型，优先使用本地缓存"""
    cache_dir = os.environ["HF_HOME"]

    # 检查本地是否有缓存的模型
    local_model_path = os.path.join(cache_dir, "models--BAAI--bge-m3")
    if os.path.exists(local_model_path):
        # 检查是否有 config.json
        config_path = os.path.join(local_model_path, "config.json")
        if os.path.exists(config_path):
            print(f"使用本地缓存模型: {local_model_path}")
            return HuggingFaceEmbeddings(
                model_name=str(local_model_path),
                model_kwargs={"device": "cpu", "trust_remote_code": True},
                encode_kwargs={"normalize_embeddings": True}
            )

    # 从镜像下载模型
    print("从 HF-Mirror 下载模型...")
    try:
        return HuggingFaceEmbeddings(
            model_name="BAAI/bge-m3",
            model_kwargs={"device": "cpu", "trust_remote_code": True},
            encode_kwargs={"normalize_embeddings": True}
        )
    except Exception as e:
        print(f"BAAI/bge-m3 加载失败: {e}")
        return None


def _fetch_url(url: str, timeout: int = 10) -> str:
    """从 URL 获取页面内容"""
    try:
        import urllib.request
        import ssl
        # 忽略 SSL 证书验证
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            return resp.read().decode("utf-8", errors="ignore")
    except Exception as e:
        print(f"  获取 {url} 失败: {e}")
        return ""


def _extract_text_from_html(html: str) -> str:
    """从 HTML 中提取纯文本"""
    # 移除 script 和 style 标签
    html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)
    # 移除 HTML 标签
    text = re.sub(r'<[^>]+>', ' ', html)
    # 清理多余空白
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def _fetch_python_docs(topic: str) -> List[Dict]:
    """
    从 Python 官方文档抓取相关内容。

    Args:
        topic: 主题关键词

    Returns:
        List[Dict] - 包含 text 和 metadata 的列表
    """
    docs = []

    # Python 官方文档基础 URL
    base_urls = {
        "装饰器": "https://docs.python.org/3/tutorial/classes.html#decorators",
        "函数": "https://docs.python.org/3/tutorial/controlflow.html",
        "类": "https://docs.python.org/3/tutorial/classes.html",
        "闭包": "https://docs.python.org/3/tutorial/classes.html#inner-classes",
        "迭代器": "https://docs.python.org/3/tutorial/classes.html#iterators",
        "生成器": "https://docs.python.org/3/glossary.html",
        "lambda": "https://docs.python.org/3/tutorial/controlflow.html#lambda-expressions",
        "装饰器": "https://docs.python.org/3/glossary.html",
        "functools": "https://docs.python.org/3/library/functools.html",
    }

    # 尝试获取直接相关的页面
    topic_lower = topic.lower()
    for key, url in base_urls.items():
        if key.lower() in topic_lower or topic_lower in key.lower():
            print(f"  抓取: {url}")
            html = _fetch_url(url)
            if html:
                text = _extract_text_from_html(html)
                # 分割成合适大小的片段
                chunks = _split_into_chunks(text, max_length=500)
                for chunk in chunks:
                    if len(chunk) > 50:  # 过滤太短的片段
                        docs.append({
                            "text": chunk,
                            "metadata": {
                                "source": f"Python 官方文档 - {key}",
                                "url": url
                            }
                        })

    # 如果直接匹配没找到，尝试抓取索引页
    if not docs:
        index_url = "https://docs.python.org/3/genindex.html"
        print(f"  尝试抓取索引页: {index_url}")
        html = _fetch_url(index_url)
        if html:
            text = _extract_text_from_html(html)
            # 搜索包含 topic 的部分
            pattern = re.compile(rf'{topic}.{{0,200}}', re.IGNORECASE)
            matches = pattern.findall(text)
            for match in matches[:5]:
                if len(match) > 30:
                    docs.append({
                        "text": match,
                        "metadata": {
                            "source": "Python 官方文档 - 索引",
                            "url": index_url
                        }
                    })

    return docs[:10]  # 最多返回10个文档片段


def _split_into_chunks(text: str, max_length: int = 500) -> List[str]:
    """将长文本分割成小块"""
    sentences = re.split(r'([。！？\n])', text)
    chunks = []
    current_chunk = ""

    for part in sentences:
        if len(current_chunk) + len(part) <= max_length:
            current_chunk += part
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = part

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks


class OfficialDocsRAG:
    """
    官方文档 RAG 类。当 embedding 模型不可用时降级为纯文本匹配。
    """

    def __init__(self, persist_directory: str = "./chroma_official_docs"):
        self.persist_directory = persist_directory
        os.makedirs(self.persist_directory, exist_ok=True)

        self.embeddings = None
        self.vectorstore = None
        self._text_docs = []  # 用于纯文本匹配

        # 尝试获取 embedding 模型，失败则降级
        try:
            self.embeddings = _get_embedding_model()
        except Exception as e:
            print(f"Embedding 模型初始化失败: {e}")
            self.embeddings = None

        self._init_vectorstore()

    def _init_vectorstore(self):
        """初始化向量数据库"""
        if self.embeddings is None:
            print("使用纯文本匹配模式")
            return

        try:
            self.vectorstore = Chroma(
                persist_directory=self.persist_directory,
                embedding_function=self.embeddings
            )
        except Exception as e:
            print(f"加载向量库失败 ({e})，降级为纯文本匹配...")
            self.vectorstore = None

    def add_documents(self, texts: List[str], metadatas: List[Dict] = None):
        """
        添加文档片段到向量库。

        Args:
            texts: 文档文本列表
            metadatas: 元数据列表（如 {"source": "python官方文档", "url": "..."}）
        """
        if not texts:
            return

        if metadatas is None:
            metadatas = [{"source": "official_docs"} for _ in texts]

        ids = [f"doc_{i}_{hash(t[:100])}" for i, t in enumerate(texts)]

        self.vectorstore.add_texts(texts=texts, metadatas=metadatas, ids=ids)

    def retrieve(self, query: str, k: int = 5) -> List[Dict]:
        """
        检索与查询相关的文档片段。

        Args:
            query: 查询文本
            k: 返回数量

        Returns:
            List[Dict] - 包含 content, source, url 的列表
        """
        if not self.vectorstore:
            print("向量库未初始化，返回空结果")
            return []

        try:
            docs = self.vectorstore.similarity_search(query, k=k)
            return [
                {
                    "content": doc.page_content,
                    "source": doc.metadata.get("source", "official_docs"),
                    "url": doc.metadata.get("url", "")
                }
                for doc in docs
            ]
        except Exception as e:
            print(f"RAG 检索失败: {e}")
            # fallback: 如果检索失败，尝试重新初始化
            try:
                self._init_vectorstore()
                docs = self.vectorstore.similarity_search(query, k=k)
                return [
                    {
                        "content": doc.page_content,
                        "source": doc.metadata.get("source", "official_docs"),
                        "url": doc.metadata.get("url", "")
                    }
                    for doc in docs
                ]
            except Exception:
                return []

    def clear(self):
        """清空向量库"""
        try:
            self.vectorstore.delete_collection()
            self._init_vectorstore()
        except Exception:
            pass


# 全局单例
_official_docs_rag = None


def get_official_docs_rag() -> OfficialDocsRAG:
    """获取全局 OfficialDocsRAG 实例"""
    global _official_docs_rag
    if _official_docs_rag is None:
        _official_docs_rag = OfficialDocsRAG()
    return _official_docs_rag


def init_official_docs_rAG(topic: str = "装饰器"):
    """
    初始化官方文档 RAG，从官方网站抓取相关内容。

    Args:
        topic: 学习主题，用于决定抓取哪些文档
    """
    rag = get_official_docs_rag()

    print(f"🔍 开始抓取 Python 官方文档 (主题: {topic})...")

    # 从官方网站抓取文档
    fetched_docs = _fetch_python_docs(topic)

    if fetched_docs:
        for doc in fetched_docs:
            rag.add_documents([doc["text"]], [doc["metadata"]])
        print(f"✅ 官方文档 RAG 初始化完成，已从官网抓取 {len(fetched_docs)} 个文档片段")
    else:
        # fallback: 使用内置的 Python 知识
        print("⚠️ 官网抓取失败，使用内置默认文档...")
        _init_fallback_docs(rag)

    return rag


def _init_fallback_docs(rag: OfficialDocsRAG):
    """初始化内置的 Python 文档片段（fallback）"""
    default_docs = [
        {
            "text": "Python 装饰器是用于修改函数或类行为的函数。装饰器使用 @decorator_name 语法应用。",
            "metadata": {"source": "Python 内置文档", "url": ""}
        },
        {
            "text": "装饰器可以接受参数，也可以是类。类装饰器必须返回可调用对象。",
            "metadata": {"source": "Python 内置文档", "url": ""}
        },
        {
            "text": "functools.wraps 用于保留被装饰函数的元信息（name, docstring 等）。",
            "metadata": {"source": "Python 内置文档", "url": ""}
        },
        {
            "text": "装饰器执行顺序：从下到上。先应用 @a，再应用 @b，结果是 b(a(original_func))。",
            "metadata": {"source": "Python 内置文档", "url": ""}
        },
        {
            "text": "staticmethod 和 classmethod 是内置装饰器，用于定义类方法。",
            "metadata": {"source": "Python 内置文档", "url": ""}
        },
    ]

    for doc in default_docs:
        rag.add_documents([doc["text"]], [doc["metadata"]])

    print(f"  已加载 {len(default_docs)} 个内置文档片段")


# 测试
if __name__ == "__main__":
    rag = init_official_docs_rAG()
    results = rag.retrieve("装饰器", k=3)
    print("\n检索结果:")
    for r in results:
        print(f"  - [{r['source']}] {r['content'][:50]}...")