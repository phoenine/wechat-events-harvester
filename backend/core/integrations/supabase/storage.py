import json
import uuid
import httpx

from core.integrations.supabase import settings


class SupabaseStorage:
    def __init__(self, bucket_key: str = "qr"):
        self.url = settings.url
        self.key = settings.service_key

        bucket_conf = settings.buckets.get(bucket_key)
        if bucket_conf is None:
            raise ValueError(
                f"Bucket configuration '{bucket_key}' not found in settings.buckets"
            )

        self.bucket = bucket_conf.name
        self.path = bucket_conf.path
        self.expires = bucket_conf.expires
        self._client = httpx.AsyncClient(timeout=30.0)

    def valid(self) -> bool:
        return bool(self.url and self.key and self.bucket)

    def _headers(self, content_type: str | None = None) -> dict[str, str]:
        h = {"Authorization": f"Bearer {self.key}", "apikey": self.key}
        if content_type:
            h["Content-Type"] = content_type
        return h

    async def upload_bytes(
        self,
        path: str,
        data: bytes,
        content_type: str = "application/octet-stream",
    ) -> str:
        url = f"{self.url}/storage/v1/object/{self.bucket}/{path}"
        resp = await self._client.post(
            url,
            headers=self._headers(content_type),
            content=data,
        )
        if resp.status_code not in (200, 201):
            raise Exception(resp.text)
        # 返回可访问 URL，而不是对象路径
        try:
            if self.expires and self.expires > 0:
                return await self.sign_url(path, self.expires)
        except Exception:
            pass
        return self.public_url(path)

    async def sign_url(self, path: str, expires: int | None = None) -> str:
        ex = expires or self.expires
        url = f"{self.url}/storage/v1/object/sign/{self.bucket}/{path}"
        body = {"expiresIn": ex}
        resp = await self._client.post(
            url,
            headers=self._headers("application/json"),
            json=body,
        )
        if resp.status_code != 200:
            raise Exception(resp.text)
        data = resp.json()
        signed = data.get("signedURL") or data.get("signedUrl") or ""
        if signed.startswith("/"):
            return f"{self.url}{signed}"
        return signed

    def public_url(self, path: str) -> str:
        return f"{self.url}/storage/v1/object/public/{self.bucket}/{path}"

    async def upload_qr(self, data: bytes) -> dict[str, str]:
        path = self.path
        if "{uuid}" in path:
            path = path.format(uuid=str(uuid.uuid4()))

        url = await self.upload_bytes(path, data, "image/png")

        return {"path": path, "url": url}


supabase_storage_qr = SupabaseStorage("qr")
supabase_storage_avatar = SupabaseStorage("avatar")
supabase_storage_articles = SupabaseStorage("articles")
