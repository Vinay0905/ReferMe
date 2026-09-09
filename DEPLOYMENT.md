# ReferMe Production Replication & Deployment Guide

This guide provides everything needed to replicate, run, and scale ReferMe in **Docker containers**, on **different databases** (Self-hosted MongoDB, MongoDB Atlas, AWS DocumentDB), and on **different cloud storage systems** (Local/Docker Volumes, AWS S3, Cloudflare R2, Google Cloud Storage, Azure Blob).

---

## 1. Quickstart: Replicate with Docker Compose (1 Command)

The fastest way to run the entire system (Frontend + Backend + MongoDB) on any Linux/Mac/Windows machine or cloud VM (AWS EC2, DigitalOcean, GCP Compute, Hetzner):

```bash
# Clone or navigate to the repository
cd ReferMe

# Start all 3 services in the background
docker compose up -d --build
```

### Verification:
- **Frontend Studio**: `http://localhost:3000`
- **Backend API & Swagger Docs**: `http://localhost:8000/docs`
- **API Health Check**: `http://localhost:8000/api/v1/health`

To inspect container logs:
```bash
docker compose logs -f backend
```

---

## 2. Replicating the Ingestion Pipeline in Docker

To seed or re-index the 20 ALLEN NEET question papers and pre-generate the 3,600 WebP question crops inside the Docker container:

```bash
docker compose exec backend python scripts/index_question_papers.py
```

All PDF papers and generated WebP question snippets are stored in the Docker volume `backend_storage`, persisting across container restarts.

---

## 3. Database Replication & Migration

ReferMe uses an async repository pattern (`BaseRepository`, `Motor`, `PyMongo`) with indexed bidirectional relationships (`tests`, `topics`, `test_topics`, `questions`, `question_topics`).

### Option A: Managed MongoDB Atlas (Current Production Setup)
1. In your `.env` or Docker environment, set:
   ```env
   MONGODB_URI=mongodb+srv://<username>:<password>@<cluster-url>/?appName=ReferMe
   MONGODB_DB_NAME=referme_neet_dev
   ```
2. Whitelist your server's outbound IP address in Atlas Network Access.

### Automated 1-Command Database Replicator (`replicate_database.py`)

ReferMe includes an automated live replication utility that connects to any source database (e.g. MongoDB Atlas) and automatically transfers all 7 collections, documents, and provisions all compound/unique indexes into the target database (e.g. Docker MongoDB or a new Atlas cluster) with zero manual work:

#### Running from Host:
```bash
# Replicate from Atlas to local Docker MongoDB:
python backend/scripts/replicate_database.py --target-uri mongodb://localhost:27017

# Replicate to another remote MongoDB cluster with clean overwrite:
python backend/scripts/replicate_database.py \
    --source-uri "mongodb+srv://user:pass@cluster1.mongodb.net" \
    --target-uri "mongodb+srv://user:pass@cluster2.mongodb.net" \
    --target-db referme_neet_prod \
    --drop \
    --sync-storage
```

#### Running inside Docker:
```bash
# Triggers the replicator container to clone Atlas into the Docker MongoDB volume:
docker compose run --rm replicator
```

---

### Supported Database Targets

#### Option A: Managed MongoDB Atlas
```env
MONGODB_URI=mongodb+srv://<username>:<password>@<cluster-url>/?appName=ReferMe
MONGODB_DB_NAME=referme_neet_dev
```

#### Option B: Self-Hosted Docker MongoDB
```env
MONGODB_URI=mongodb://mongodb:27017
MONGODB_DB_NAME=referme_neet_dev
```

#### Option C: AWS DocumentDB (Amazon Managed Mongo-compatible DB)
1. Download RDS CA bundle: `wget https://truststore.pki.rds.amazonaws.com/global/global-bundle.pem`
2. Set URI with TLS parameters:
```env
MONGODB_URI=mongodb://<user>:<password>@<cluster-endpoint>:27017/?tls=true&tlsCAFile=/app/global-bundle.pem&replicaSet=rs0&readPreference=secondaryPreferred&retryWrites=false
```

---

## 4. Cloud Object Storage Migration (S3 / R2 / GCS / Azure)

Currently, ReferMe uses local filesystem volume storage (`storage_data/test_<id>/questions/q_<num>.webp`). This is the fastest setup ($< 1\text{ms}$ file responses). When scaling to multi-instance Kubernetes or Cloud Run, you can point to object storage or a CDN.

### Option A: AWS S3 or Cloudflare R2
1. Sync local artifacts to S3/R2 bucket:
   ```bash
   aws s3 sync backend/storage_data s3://my-referme-assets/storage_data --content-type "image/webp"
   ```
2. Enable Cloudflare CDN or AWS CloudFront in front of the bucket.
3. In `frontend/.env.local`, configure image CDN base URL or let FastAPI redirect:
   ```env
   NEXT_PUBLIC_CDN_URL=https://cdn.referme.com/storage_data
   ```

### Option B: Persistent Network File System (NFS / AWS EFS)
If running on AWS ECS or Kubernetes (EKS/GKE):
- Mount an AWS Elastic File System (EFS) or persistent volume claim (PVC) directly to `/app/storage_data`.
- Both the ingestion worker and API containers read and write to the exact same shared high-performance volume.

---

## 5. Production Cloud Deployment Blueprints

### A. Deploy to Fly.io / Railway / Render
1. Push your repository to GitHub.
2. Deploy backend using `backend/Dockerfile` with persistent disk mounted at `/app/storage_data`.
3. Set environment variables:
   - `MONGODB_URI`
   - `ENVIRONMENT=production`
4. Deploy frontend using `frontend/Dockerfile` or as a standard Vercel Next.js project.

### B. Deploy to AWS ECS Fargate or Kubernetes
1. **Frontend**: Deploy as ECS Task / Deployment with Service port 3000.
2. **Backend**: Deploy with mounted EFS Volume at `/app/storage_data`.
3. **Ingestion Job**: Run `scripts/index_question_papers.py` as an ECS Scheduled Task or Kubernetes Job.

---

## 6. Environment Variables Reference

| Variable | Default | Purpose |
| :--- | :--- | :--- |
| `MONGODB_URI` | `mongodb://mongodb:27017` | MongoDB connection string (Atlas or Docker) |
| `MONGODB_DB_NAME` | `referme_neet_dev` | Target database name |
| `LOCAL_STORAGE_DIR` | `./storage_data` | Directory where question papers and crops live |
| `API_V1_STR` | `/api/v1` | API version prefix |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000/api/v1` | Backend API URL accessed by the Next.js browser app |
