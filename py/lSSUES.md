# ISSUE HISTORY	

## SSL Certificate Verification Error in Python Socket

Installed system certificate support with:
```bash
python -m pip install pip-system-certs --use-feature=truststore
```
	
- Python’s default SSL verification failed because it used its own CA bundle instead of the system’s certificates.
- Installing pip-system-certs and enabling --use-feature=truststore made Python use the OS trust store.
- This resolved the TLS certificate verification errors when wrapping sockets with SSL.

## SSL Error When Wrapping Socket Before Connection

```bash
AttributeError: 'NoneType' object has no attribute 'get_unverified_chain'
```

The ssl.wrap_socket() function was called before establishing the TCP connection with socket.connect().
Because no connection existed yet, the internal _sslobj remained None, causing truststore to fail when verifying the certificate chain.

Connect first, then wrap the socket for TLS:
```python
s.connect((self.host, self.port))
if self.scheme == 'https':
    ctx = ssl.create_default_context()
    s = ctx.wrap_socket(s, server_hostname=self.host)
```

- Calling wrap_socket() before connect() leaves the SSL context uninitialized.
- Establishing the TCP connection first ensures proper TLS handshake.
- The error disappeared after correcting the call order.
