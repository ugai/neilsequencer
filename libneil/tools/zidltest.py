#!/usr/bin/env python3
# encoding: latin-1
# zzub IDL parser test

import os

ret = os.system('./zidl --c-header test_zidl.h libzzub.zidl')
if ret != 0:
	raise SystemExit(1)

data = file("test_zidl.h","r").read()
print(data)

