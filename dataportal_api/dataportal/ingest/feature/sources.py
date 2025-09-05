import ftplib, time, tempfile, os

def ftp_connect(host, retries=3, delay=2):
    for i in range(retries):
        try:
            ftp = ftplib.FTP(host); ftp.login(); return ftp
        except ftplib.all_errors:
            if i < retries-1: time.sleep(delay)
            else: raise

def load_protein_seqs(ftp, faa_path):
    seqs, cur, buf = {}, None, []
    with tempfile.NamedTemporaryFile(mode="w+b", delete=False) as tmp:
        ftp.retrbinary(f"RETR {faa_path}", tmp.write)
        tmp.flush(); tmp.seek(0)
        for raw in tmp:
            line = raw.decode("utf-8").strip()
            if line.startswith(">"):
                if cur: seqs[cur] = "".join(buf); buf = []
                cur = line.split()[0][1:]
            elif line:
                buf.append(line)
        if cur: seqs[cur] = "".join(buf)
    os.unlink(tmp.name)
    return seqs
