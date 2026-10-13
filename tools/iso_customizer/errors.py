"""Dinh nghia loi cua ISO Customizer.

Moi loi mang mot ma thoat (exit code) rieng de CLI va CI phan biet duoc
nhom that bai ma khong can phan tich chuoi thong bao.
"""


class CustomizerError(Exception):
    """Loi nghiep vu co the bao truoc duoc. Mac dinh exit code 1."""

    exit_code = 1


class UsageError(CustomizerError):
    """Dau vao cua nguoi dung khong hop le."""

    exit_code = 2


class EnvValidationError(CustomizerError):
    """Moi truong build khong dap ung yeu cau."""

    exit_code = 3


class SourceIsoError(CustomizerError):
    """ISO nguon khong hop le hoac khong tuong thich."""

    exit_code = 4


class IntegrationError(CustomizerError):
    """Thanh phan giao dien chua san sang hoac tich hop that bai."""

    exit_code = 5


class BuildStepError(CustomizerError):
    """Mot buoc remaster ben ngoai that bai."""

    exit_code = 6
