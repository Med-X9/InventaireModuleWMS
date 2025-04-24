from apps.masterdata.models import Account
from typing import List

class AccountService:
    @staticmethod
    def get_all_accounts() -> List[Account]:
        """
        Récupère tous les comptes
        """
        return Account.objects.all() 