import logging
from rest_framework import views, viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from .models import GameWallet, GameTransaction
from .serializers import GameWalletSerializer, GameWalletBalanceSerializer, GameTransactionSerializer

logger = logging.getLogger(__name__)


class GameWalletViewSet(viewsets.ViewSet):
    """API endpoints for game wallet management."""
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get_game_wallet(self, user):
        """Get or create game wallet for user."""
        wallet, created = GameWallet.objects.get_or_create(user=user)
        if created:
            logger.info(f"Created new game wallet for user {user.username}")
        return wallet

    @action(detail=False, methods=['get'])
    def balance(self, request):
        """Get current wallet balance and stats."""
        try:
            wallet = self.get_game_wallet(request.user)
            serializer = GameWalletBalanceSerializer(wallet)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error fetching balance: {str(e)}", exc_info=True)
            return Response(
                {'detail': f'Error fetching balance: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def transactions(self, request):
        """Get transaction history for the wallet."""
        try:
            wallet = self.get_game_wallet(request.user)
            
            # Get query params for filtering
            limit = int(request.query_params.get('limit', 50))
            transaction_type = request.query_params.get('type', None)
            
            # Build query
            transactions = wallet.transactions.all()
            if transaction_type:
                transactions = transactions.filter(transaction_type=transaction_type)
            
            transactions = transactions[:limit]
            
            serializer = GameTransactionSerializer(transactions, many=True)
            return Response({
                'count': len(serializer.data),
                'results': serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error fetching transactions: {str(e)}", exc_info=True)
            return Response(
                {'detail': f'Error fetching transactions: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def full(self, request):
        """Get full wallet info including transaction history."""
        try:
            wallet = self.get_game_wallet(request.user)
            serializer = GameWalletSerializer(wallet)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error fetching wallet: {str(e)}", exc_info=True)
            return Response(
                {'detail': f'Error fetching wallet: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class GameWalletSimpleView(views.APIView):
    """Simple view for getting wallet balance without authentication (for initial load)."""
    
    def get(self, request):
        """Get wallet balance if user is authenticated."""
        if not request.user.is_authenticated:
            return Response({'balance': 0}, status=status.HTTP_200_OK)
        
        try:
            wallet, _ = GameWallet.objects.get_or_create(user=request.user)
            return Response({
                'balance': float(wallet.balance),
                'total_deposits': float(wallet.total_deposits),
                'total_winnings': float(wallet.total_winnings),
                'total_losses': float(wallet.total_losses),
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error fetching balance: {str(e)}", exc_info=True)
            return Response({'balance': 0}, status=status.HTTP_200_OK)
