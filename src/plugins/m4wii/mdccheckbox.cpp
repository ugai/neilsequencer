// Machine generated IDispatch wrapper class(es) created by Microsoft Visual C++

// NOTE: Do not modify the contents of this file.  If this class is regenerated by
//  Microsoft Visual C++, your modifications will be overwritten.


#include "stdafx.h"
#include "mdccheckbox.h"

/////////////////////////////////////////////////////////////////////////////
// CMdcCheckBox

IMPLEMENT_DYNCREATE(CMdcCheckBox, CWnd)

/////////////////////////////////////////////////////////////////////////////
// CMdcCheckBox properties

/////////////////////////////////////////////////////////////////////////////
// CMdcCheckBox operations

void CMdcCheckBox::SetAccelerator(LPCTSTR lpszNewValue)
{
	static BYTE parms[] =
		VTS_BSTR;
	InvokeHelper(0xfffffde1, DISPATCH_PROPERTYPUT, VT_EMPTY, NULL, parms,
		 lpszNewValue);
}

CString CMdcCheckBox::GetAccelerator()
{
	CString result;
	InvokeHelper(0xfffffde1, DISPATCH_PROPERTYGET, VT_BSTR, (void*)&result, NULL);
	return result;
}

void CMdcCheckBox::SetAlignment(long nNewValue)
{
	static BYTE parms[] =
		VTS_I4;
	InvokeHelper(0x2c6, DISPATCH_PROPERTYPUT, VT_EMPTY, NULL, parms,
		 nNewValue);
}

long CMdcCheckBox::GetAlignment()
{
	long result;
	InvokeHelper(0x2c6, DISPATCH_PROPERTYGET, VT_I4, (void*)&result, NULL);
	return result;
}

void CMdcCheckBox::SetAutoSize(BOOL bNewValue)
{
	static BYTE parms[] =
		VTS_BOOL;
	InvokeHelper(0xfffffe0c, DISPATCH_PROPERTYPUT, VT_EMPTY, NULL, parms,
		 bNewValue);
}

BOOL CMdcCheckBox::GetAutoSize()
{
	BOOL result;
	InvokeHelper(0xfffffe0c, DISPATCH_PROPERTYGET, VT_BOOL, (void*)&result, NULL);
	return result;
}

void CMdcCheckBox::SetBackColor(long nNewValue)
{
	static BYTE parms[] =
		VTS_I4;
	InvokeHelper(DISPID_BACKCOLOR, DISPATCH_PROPERTYPUT, VT_EMPTY, NULL, parms,
		 nNewValue);
}

long CMdcCheckBox::GetBackColor()
{
	long result;
	InvokeHelper(DISPID_BACKCOLOR, DISPATCH_PROPERTYGET, VT_I4, (void*)&result, NULL);
	return result;
}

void CMdcCheckBox::SetBackStyle(long nNewValue)
{
	static BYTE parms[] =
		VTS_I4;
	InvokeHelper(0xfffffe0a, DISPATCH_PROPERTYPUT, VT_EMPTY, NULL, parms,
		 nNewValue);
}

long CMdcCheckBox::GetBackStyle()
{
	long result;
	InvokeHelper(0xfffffe0a, DISPATCH_PROPERTYGET, VT_I4, (void*)&result, NULL);
	return result;
}

void CMdcCheckBox::SetCaption(LPCTSTR lpszNewValue)
{
	static BYTE parms[] =
		VTS_BSTR;
	InvokeHelper(DISPID_CAPTION, DISPATCH_PROPERTYPUT, VT_EMPTY, NULL, parms,
		 lpszNewValue);
}

CString CMdcCheckBox::GetCaption()
{
	CString result;
	InvokeHelper(DISPID_CAPTION, DISPATCH_PROPERTYGET, VT_BSTR, (void*)&result, NULL);
	return result;
}

void CMdcCheckBox::SetEnabled(BOOL bNewValue)
{
	static BYTE parms[] =
		VTS_BOOL;
	InvokeHelper(DISPID_ENABLED, DISPATCH_PROPERTYPUT, VT_EMPTY, NULL, parms,
		 bNewValue);
}

BOOL CMdcCheckBox::GetEnabled()
{
	BOOL result;
	InvokeHelper(DISPID_ENABLED, DISPATCH_PROPERTYGET, VT_BOOL, (void*)&result, NULL);
	return result;
}

void CMdcCheckBox::SetRefFont(LPDISPATCH newValue)
{
	static BYTE parms[] =
		VTS_DISPATCH;
	InvokeHelper(DISPID_FONT, DISPATCH_PROPERTYPUTREF, VT_EMPTY, NULL, parms,
		 newValue);
}

LPDISPATCH CMdcCheckBox::GetFont()
{
	LPDISPATCH result;
	InvokeHelper(DISPID_FONT, DISPATCH_PROPERTYGET, VT_DISPATCH, (void*)&result, NULL);
	return result;
}

void CMdcCheckBox::SetForeColor(long nNewValue)
{
	static BYTE parms[] =
		VTS_I4;
	InvokeHelper(DISPID_FORECOLOR, DISPATCH_PROPERTYPUT, VT_EMPTY, NULL, parms,
		 nNewValue);
}

long CMdcCheckBox::GetForeColor()
{
	long result;
	InvokeHelper(DISPID_FORECOLOR, DISPATCH_PROPERTYGET, VT_I4, (void*)&result, NULL);
	return result;
}

void CMdcCheckBox::SetLocked(BOOL bNewValue)
{
	static BYTE parms[] =
		VTS_BOOL;
	InvokeHelper(0xa, DISPATCH_PROPERTYPUT, VT_EMPTY, NULL, parms,
		 bNewValue);
}

BOOL CMdcCheckBox::GetLocked()
{
	BOOL result;
	InvokeHelper(0xa, DISPATCH_PROPERTYGET, VT_BOOL, (void*)&result, NULL);
	return result;
}

void CMdcCheckBox::SetMouseIcon(LPDISPATCH newValue)
{
	static BYTE parms[] =
		VTS_DISPATCH;
	InvokeHelper(0xfffffdf6, DISPATCH_PROPERTYPUT, VT_EMPTY, NULL, parms,
		 newValue);
}

void CMdcCheckBox::SetRefMouseIcon(LPDISPATCH newValue)
{
	static BYTE parms[] =
		VTS_DISPATCH;
	InvokeHelper(0xfffffdf6, DISPATCH_PROPERTYPUTREF, VT_EMPTY, NULL, parms,
		 newValue);
}

LPDISPATCH CMdcCheckBox::GetMouseIcon()
{
	LPDISPATCH result;
	InvokeHelper(0xfffffdf6, DISPATCH_PROPERTYGET, VT_DISPATCH, (void*)&result, NULL);
	return result;
}

void CMdcCheckBox::SetMousePointer(long nNewValue)
{
	static BYTE parms[] =
		VTS_I4;
	InvokeHelper(0xfffffdf7, DISPATCH_PROPERTYPUT, VT_EMPTY, NULL, parms,
		 nNewValue);
}

long CMdcCheckBox::GetMousePointer()
{
	long result;
	InvokeHelper(0xfffffdf7, DISPATCH_PROPERTYGET, VT_I4, (void*)&result, NULL);
	return result;
}

void CMdcCheckBox::SetPicture(LPDISPATCH newValue)
{
	static BYTE parms[] =
		VTS_DISPATCH;
	InvokeHelper(0xfffffdf5, DISPATCH_PROPERTYPUT, VT_EMPTY, NULL, parms,
		 newValue);
}

void CMdcCheckBox::SetRefPicture(LPDISPATCH newValue)
{
	static BYTE parms[] =
		VTS_DISPATCH;
	InvokeHelper(0xfffffdf5, DISPATCH_PROPERTYPUTREF, VT_EMPTY, NULL, parms,
		 newValue);
}

LPDISPATCH CMdcCheckBox::GetPicture()
{
	LPDISPATCH result;
	InvokeHelper(0xfffffdf5, DISPATCH_PROPERTYGET, VT_DISPATCH, (void*)&result, NULL);
	return result;
}

void CMdcCheckBox::SetPicturePosition(long nNewValue)
{
	static BYTE parms[] =
		VTS_I4;
	InvokeHelper(0xb, DISPATCH_PROPERTYPUT, VT_EMPTY, NULL, parms,
		 nNewValue);
}

long CMdcCheckBox::GetPicturePosition()
{
	long result;
	InvokeHelper(0xb, DISPATCH_PROPERTYGET, VT_I4, (void*)&result, NULL);
	return result;
}

void CMdcCheckBox::SetSpecialEffect(long nNewValue)
{
	static BYTE parms[] =
		VTS_I4;
	InvokeHelper(0xc, DISPATCH_PROPERTYPUT, VT_EMPTY, NULL, parms,
		 nNewValue);
}

long CMdcCheckBox::GetSpecialEffect()
{
	long result;
	InvokeHelper(0xc, DISPATCH_PROPERTYGET, VT_I4, (void*)&result, NULL);
	return result;
}

void CMdcCheckBox::SetTripleState(BOOL bNewValue)
{
	static BYTE parms[] =
		VTS_BOOL;
	InvokeHelper(0x2bc, DISPATCH_PROPERTYPUT, VT_EMPTY, NULL, parms,
		 bNewValue);
}

BOOL CMdcCheckBox::GetTripleState()
{
	BOOL result;
	InvokeHelper(0x2bc, DISPATCH_PROPERTYGET, VT_BOOL, (void*)&result, NULL);
	return result;
}

void CMdcCheckBox::SetValue(VARIANT* newValue)
{
	static BYTE parms[] =
		VTS_PVARIANT;
	InvokeHelper(0x0, DISPATCH_PROPERTYPUT, VT_EMPTY, NULL, parms,
		 newValue);
}

VARIANT CMdcCheckBox::GetValue()
{
	VARIANT result;
	InvokeHelper(0x0, DISPATCH_PROPERTYGET, VT_VARIANT, (void*)&result, NULL);
	return result;
}

void CMdcCheckBox::SetWordWrap(BOOL bNewValue)
{
	static BYTE parms[] =
		VTS_BOOL;
	InvokeHelper(0xfffffde8, DISPATCH_PROPERTYPUT, VT_EMPTY, NULL, parms,
		 bNewValue);
}

BOOL CMdcCheckBox::GetWordWrap()
{
	BOOL result;
	InvokeHelper(0xfffffde8, DISPATCH_PROPERTYGET, VT_BOOL, (void*)&result, NULL);
	return result;
}

void CMdcCheckBox::SetGroupName(LPCTSTR lpszNewValue)
{
	static BYTE parms[] =
		VTS_BSTR;
	InvokeHelper(0xfffffde3, DISPATCH_PROPERTYPUT, VT_EMPTY, NULL, parms,
		 lpszNewValue);
}

CString CMdcCheckBox::GetGroupName()
{
	CString result;
	InvokeHelper(0xfffffde3, DISPATCH_PROPERTYGET, VT_BSTR, (void*)&result, NULL);
	return result;
}

void CMdcCheckBox::SetTextAlign(long nNewValue)
{
	static BYTE parms[] =
		VTS_I4;
	InvokeHelper(0x2714, DISPATCH_PROPERTYPUT, VT_EMPTY, NULL, parms,
		 nNewValue);
}

long CMdcCheckBox::GetTextAlign()
{
	long result;
	InvokeHelper(0x2714, DISPATCH_PROPERTYGET, VT_I4, (void*)&result, NULL);
	return result;
}
