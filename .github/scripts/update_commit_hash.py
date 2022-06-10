import os
import subprocess
import requests
from typing import Any

PYTORCH_REPO = "https://api.github.com/repos/pytorch/pytorch"
GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
REQUEST_HEADERS = {
    "Accept": "application/vnd.github.v3+json",
    "Authorization": "token " + GITHUB_TOKEN,
}
owner, repo = "clee2000", "pytorch"


def parse_args() -> Any:
    from argparse import ArgumentParser

    parser = ArgumentParser("Rebase PR into branch")
    parser.add_argument("--repo-name", type=str)
    parser.add_argument("--branch", type=str)
    return parser.parse_args()


def make_pr(repo_name, branch_name) -> Any:
    params = {
        "title": f"[{repo_name} hash update] update the pinned {repo_name} hash",
        "head": branch_name,
        "body": "This PR is auto - generated nightly by[this action](https://github.com/pytorch/pytorch/blob/master/.github/workflows/_update-commit-hash.yml).\nUpdate the pinned {args.repo_name} hash.",
    }
    response = requests.get(
        f"https://api.github.com/repos/{owner}/{repo}/pulls",
        params=params,
        headers=REQUEST_HEADERS,
    ).json()
    print(f"made pr {response.number}")
    return response.number


def approve_pr(pr_number):
    params = {"event": "APRROVE"}
    requests.get(
        f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/reviews",
        params=params,
        headers=REQUEST_HEADERS,
    )


def make_comment(pr_number):
    params = {"body": "a;dlsfkj"}
    requests.get(
        f"https://api.github.com/repos/{owner}/{repo}/issues/{pr_number}/comments",
        params=params,
        headers=REQUEST_HEADERS,
    )


def main() -> None:
    args = parse_args()

    branch_name = os.environ["NEW_BRANCH_NAME"]

    # query to see if a pr already exists
    params = {
        "q": f"is:pr is:open in:title author:clee2000 repo:clee2000/pytorch {args.repo_name} hash update"
    }
    response = requests.get(
        "https://api.github.com/search/issues", params=params, headers=REQUEST_HEADERS
    ).json()
    if response["total_count"] != 0:
        # pr does exist
        pr_num = response["items"][0]["number"]
        response = requests.get(
            f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_num}",
            headers=REQUEST_HEADERS,
        ).json()
        branch_name = response["head"]["ref"]
        print(f"pr does exist, number is {pr_num}, branch name is {branch_name}")

    # update file
    command = f"pushd {args.repo_name} && git rev-parse {args.branch} > ../.github/{args.repo_name}_commit_hash.txt"
    subprocess.run(command.split(), executable="/bin/bash")
    retcode = subprocess.run(
        f"git diff --exit-code .github/{args.repo_name}_commit_hash.txt".split()
    ).returncode
    if retcode == 1:
        # if there was an update, push to the branch
        subprocess.run(
            f"git config --global user.email 'pytorchmergebot@users.noreply.github.com'".split()
        )
        subprocess.run(f"git config --global user.name".split() + ["PyTorch MergeBot"])
        subprocess.run(f"git checkout -b {branch_name}".split())
        subprocess.run(f"git add .github/{args.repo_name}_commit_hash.txt".split())
        subprocess.run(f"git add .github/{args.repo_name}_commit_hash.txt".split())
        subprocess.run(
            f"git commit -m".split() + [f"update {args.repo_name} commit hash"]
        )
        subprocess.run(f"git push --set-upstream origin {branch_name} -f".split())
        print(f"changes pushed to branch {branch_name}")
        if pr_num is None:
            pr_num = make_pr(args.repo_name, branch_name)
    if pr_num != None:
        make_comment(pr_num)


if __name__ == "__main__":
    main()
