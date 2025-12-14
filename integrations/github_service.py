import httpx
from config import settings

async def create_github_issue(repo_owner: str, repo_name: str, title: str, body: str, access_token: str):
    """Создание issue в GitHub репозитории"""
    url = f"{settings.GITHUB_API_URL}/repos/{repo_owner}/{repo_name}/issues"
    
    headers = {
        "Authorization": f"token {access_token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    payload = {
        "title": title,
        "body": body
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=payload)
        if response.status_code == 201:
            return response.json()
        else:
            raise Exception(f"GitHub API error: {response.text}")

async def get_github_issues(repo_owner: str, repo_name: str, access_token: str):
    """Получение списка issues из GitHub репозитория"""
    url = f"{settings.GITHUB_API_URL}/repos/{repo_owner}/{repo_name}/issues"
    
    headers = {
        "Authorization": f"token {access_token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"GitHub API error: {response.text}")

async def sync_github_issues_to_tasks(repo_owner: str, repo_name: str, access_token: str, project_id: str):
    """Синхронизация GitHub issues с задачами проекта"""
    issues = await get_github_issues(repo_owner, repo_name, access_token)
    
    # Здесь можно добавить логику создания задач из issues
    # Для этого нужно вызвать tasks service API
    
    return issues
