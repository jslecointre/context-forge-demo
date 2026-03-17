if __name__ == "__main__":
    import uvicorn
    from dotenv import load_dotenv

    load_dotenv()
    uvicorn.run(
        "backend.app:app", host="0.0.0.0", port=8002, reload=True, log_level="debug"
    )
