"""MintOS Glass ISO Customizer.

Cong cu lay ISO Linux Mint goc, tich hop giao dien MintOS Glass va tao ISO moi.
Chi dung Python standard library cho logic cua chinh cong cu; cac buoc remaster
(extract, squashfs, ghi ISO) duoc thuc hien bang cong cu he thong ben ngoai khi
chung thuc su ton tai tren may build, va bi chan som neu khong ton tai.

Trang thai kiem chung duoc ghi trung thuc trong tung bao cao: kiem tra tinh
duoc file/cau truc ISO khong co nghia la ISO da boot hoac cai dat thanh cong.
"""

__version__ = "0.1.0"
TOOL_NAME = "mintos-glass-iso"
WORKSPACE_MARKER = ".mintos-glass-workspace"
