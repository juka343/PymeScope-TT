import os
import uuid
from pathlib import Path

from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore, storage


def main() -> None:
    load_dotenv()
    credentials_path = os.getenv("FIREBASE_CREDENTIALS_PATH")
    bucket_name = os.getenv("FIREBASE_STORAGE_BUCKET")

    if not credentials_path or not bucket_name:
        raise RuntimeError("FIREBASE_CREDENTIALS_PATH or FIREBASE_STORAGE_BUCKET missing in .env")

    pdf_path = os.getenv("PDF_PATH")
    if not pdf_path:
        raise RuntimeError("Set PDF_PATH env var to the local PDF path")

    if not Path(pdf_path).exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    if not firebase_admin._apps:
        cred = credentials.Certificate(credentials_path)
        firebase_admin.initialize_app(cred, {"storageBucket": bucket_name})

    db = firestore.client()
    bucket = storage.bucket()

    user_id = f"user_{uuid.uuid4().hex[:8]}"
    company_id = f"company_{uuid.uuid4().hex[:8]}"
    analysis_id = str(uuid.uuid4())
    statement_id = str(uuid.uuid4())
    period = os.getenv("PERIOD", "2026")

    file_name = Path(pdf_path).name
    storage_path = f"analyses/{analysis_id}/{statement_id}/{file_name}"

    blob = bucket.blob(storage_path)
    blob.upload_from_filename(pdf_path)

    analysis_ref = (
        db.collection("users")
        .document(user_id)
        .collection("companies")
        .document(company_id)
        .collection("analysisSessions")
        .document(analysis_id)
    )

    analysis_ref.set(
        {
            "ownerId": user_id,
            "companyId": company_id,
            "period": period,
            "status": "uploaded",
            "createdAt": firestore.SERVER_TIMESTAMP,
            "updatedAt": firestore.SERVER_TIMESTAMP,
        }
    )

    statement_ref = analysis_ref.collection("financialStatements").document(statement_id)
    statement_ref.set(
        {
            "analysisId": analysis_id,
            "companyId": company_id,
            "period": period,
            "statementType": "Balance General",
            "version": 1,
            "storagePath": storage_path,
            "storageBucket": bucket_name,
            "createdAt": firestore.SERVER_TIMESTAMP,
            "updatedAt": firestore.SERVER_TIMESTAMP,
            "status": "uploaded",
        }
    )

    print("Upload and Firestore registration complete.")
    print(f"userId: {user_id}")
    print(f"companyId: {company_id}")
    print(f"analysisId: {analysis_id}")
    print(f"statementId: {statement_id}")
    print(f"storagePath: {storage_path}")


if __name__ == "__main__":
    main()
