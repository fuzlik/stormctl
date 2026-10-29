# stormctl

TeamStorm from the terminal. Every workspace, not just one.

`stormctl` is a small Python client for the TeamStorm public API. It finds tasks across spaces, opens a card by its key, and sets start and due dates. No extra libraries.

## Setup

Python 3.9 or newer. Copy the env file and fill in your own host and token:

```bash
cp .env.example .env
```

```
TEAMSTORM_API_URL=https://your-teamstorm-host
TEAMSTORM_API_TOKEN=your-private-token
```

The token is a PrivateToken from your TeamStorm profile. The URL is only the host, without `/cwm/public/api/v1`.

## Use

Run it from this folder:

```bash
python3 -m ts workspaces
python3 -m ts find text
python3 -m ts find --assignee ivan
python3 -m ts users ivan
python3 -m ts folders KEY
python3 -m ts tasks KEY <folder-id>
python3 -m ts show KEY-1
python3 -m ts due KEY-1 2026-11-02 2026-11-06
```

A task key already names its workspace: `KEY-1` is space `KEY`, item `1`.

Any raw API call works too:

```bash
python3 -m ts GET /workspaces
python3 -m ts PATCH /workspaces/KEY/workitems/KEY-1 '{"name":"New name"}'
```

## What it does not keep

The client does not store your tasks, spaces, or descriptions. Connection settings stay in `.env` on your machine. That file is not part of this repository.
