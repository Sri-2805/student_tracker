from flask_sqlalchemy import SQLAlchemy

# Ensure compatibility with newer Werkzeug where `url_decode` may be missing
try:
	# Prefer importing the real implementations if available
	from werkzeug.urls import url_decode, url_encode  # type: ignore
except Exception:
	# Provide a minimal shim that behaves like werkzeug.urls.url_decode
	from urllib.parse import parse_qsl

	def url_decode(s, charset="utf-8", errors="replace", keep_blank_values=False, encoding=None):
		if isinstance(s, bytes):
			s = s.decode(charset, errors)
		return dict(parse_qsl(s, keep_blank_values=keep_blank_values, encoding=encoding or charset))

	# Provide a minimal shim for url_encode that accepts common kwargs
	from urllib.parse import urlencode as _urlencode

	def url_encode(obj, charset="utf-8", sort=False, **kwargs):
		# Convert mappings to sequence of pairs when sorting is requested
		if hasattr(obj, "items") and sort:
			items = sorted(obj.items())
		elif hasattr(obj, "items"):
			items = obj.items()
		else:
			items = obj
		# Use doseq if provided in kwargs, default to True for multiple values
		doseq = kwargs.get("doseq", True)
		return _urlencode(list(items), doseq=doseq)

	# Inject into the werkzeug.urls module so downstream imports succeed
	import importlib

	try:
		urls_mod = importlib.import_module("werkzeug.urls")
		setattr(urls_mod, "url_decode", url_decode)
		setattr(urls_mod, "url_encode", url_encode)
	except Exception:
		# If injection fails, continue; the local shim will still be available
		pass

from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = "Please log in to access the LMS dashboard."
login_manager.login_message_category = "info"
