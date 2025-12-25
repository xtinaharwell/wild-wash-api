import logging
from rest_framework import views, viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from .models import GameWallet, GameTransaction, SpinAlgorithmConfiguration
from .serializers import GameWalletSerializer, GameWalletBalanceSerializer, GameTransactionSerializer, SpinAlgorithmConfigurationSerializer
from .algorithms import get_algorithm, get_all_algorithms

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

    @action(detail=False, methods=['post'])
    def spin(self, request):
        """Perform a spin using the active algorithm.
        
        The spin cost is deducted and winnings are calculated based on the algorithm result.
        
        Request body:
        {
            "spin_cost": 20  (optional, defaults to SPIN_COST)
        }
        
        Returns the spin result with algorithm-determined outcome.
        """
        try:
            from decimal import Decimal
            
            SPIN_COST = Decimal('20')  # Default spin cost
            
            wallet = self.get_game_wallet(request.user)
            spin_cost = Decimal(str(request.data.get('spin_cost', SPIN_COST)))
            
            # Check if user has sufficient balance
            if wallet.balance < spin_cost:
                return Response(
                    {'detail': f'Insufficient balance. Required: {spin_cost}, Available: {wallet.balance}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get active algorithm
            active_config = SpinAlgorithmConfiguration.objects.filter(is_active=True).first()
            if not active_config:
                return Response(
                    {'detail': 'No spin algorithm is currently configured'},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
            
            # Get algorithm and perform spin
            algorithm = get_algorithm(active_config.algorithm_key)
            result = algorithm.spin()
            
            # Calculate winnings (convert multiplier to Decimal to avoid type mismatch)
            multiplier = Decimal(str(result['multiplier']))
            winnings = spin_cost * multiplier
            
            # Deduct spin cost
            wallet.deduct_funds(
                spin_cost,
                reason='spin',
                notes=f'Spin cost using {active_config.name} algorithm'
            )
            
            # Add winnings if won
            if result['multiplier'] > 0:
                wallet.add_winnings(
                    winnings,
                    game_name='Lucky Spin Wheel',
                    notes=f'Won {result["label"]} (multiplier {result["multiplier"]}x) using {active_config.name}'
                )
            
            # Return result
            return Response({
                'result': result,
                'spin_cost': float(spin_cost),
                'winnings': float(winnings),
                'net_result': float(winnings - spin_cost),
                'balance': float(wallet.balance),
                'total_deposits': float(wallet.total_deposits),
                'total_winnings': float(wallet.total_winnings),
                'total_losses': float(wallet.total_losses),
                'algorithm_used': active_config.name,
                'message': f'Spin result: {result["label"]}. Net: {float(winnings - spin_cost):+.0f} KES'
            }, status=status.HTTP_200_OK)
            
        except ValueError as e:
            return Response(
                {'detail': f'Invalid input: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error performing spin: {str(e)}", exc_info=True)
            return Response(
                {'detail': f'Error performing spin: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def multi_spin(self, request):
        """Perform multiple spins in one request.
        
        Request body:
        {
            "num_spins": 5,
            "spin_cost": 20
        }
        
        Returns list of all spin results and final balance.
        """
        try:
            from decimal import Decimal
            
            SPIN_COST = Decimal('20')
            wallet = self.get_game_wallet(request.user)
            
            # Get parameters
            num_spins = int(request.data.get('num_spins', 5))
            spin_cost = Decimal(str(request.data.get('spin_cost', SPIN_COST)))
            
            # Validate
            if num_spins < 1 or num_spins > 100:
                return Response(
                    {'detail': 'Number of spins must be between 1 and 100'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if spin_cost <= 0:
                return Response(
                    {'detail': 'Spin cost must be positive'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            total_cost = spin_cost * num_spins
            
            # Check if user has sufficient balance
            if wallet.balance < total_cost:
                return Response(
                    {
                        'detail': f'Insufficient balance. Required: {total_cost}, Available: {wallet.balance}',
                        'required': float(total_cost),
                        'available': float(wallet.balance)
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get active algorithm
            active_config = SpinAlgorithmConfiguration.objects.filter(is_active=True).first()
            if not active_config:
                return Response(
                    {'detail': 'No spin algorithm is currently configured'},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
            
            # Perform all spins
            algorithm = get_algorithm(active_config.algorithm_key)
            spin_results = []
            total_winnings = Decimal('0')
            
            for i in range(num_spins):
                # Perform spin
                result = algorithm.spin()
                # Convert multiplier to Decimal to ensure proper arithmetic
                multiplier = Decimal(str(result['multiplier']))
                winnings = spin_cost * multiplier
                total_winnings += winnings
                
                spin_results.append({
                    'spin_number': i + 1,
                    'result': result,
                    'spin_cost': float(spin_cost),
                    'winnings': float(winnings),
                    'net_result': float(winnings - spin_cost)
                })
            
            # Deduct all spin costs at once
            wallet.deduct_funds(
                total_cost,
                reason='multi_spin',
                notes=f'Multi-spin: {num_spins} spins at {spin_cost} each'
            )
            
            # Add all winnings at once
            if total_winnings > 0:
                wallet.add_winnings(
                    total_winnings,
                    game_name='Lucky Spin Wheel',
                    notes=f'Multi-spin winnings: {num_spins} spins using {active_config.name}'
                )
            
            # Calculate statistics
            net_result = total_winnings - total_cost
            wins = sum(1 for r in spin_results if r['result']['multiplier'] > 1)
            losses = sum(1 for r in spin_results if r['result']['multiplier'] == 0)
            breaks_even = num_spins - wins - losses
            
            return Response({
                'spins': spin_results,
                'summary': {
                    'total_spins': num_spins,
                    'total_cost': float(total_cost),
                    'total_winnings': float(total_winnings),
                    'net_result': float(net_result),
                    'wins': wins,
                    'losses': losses,
                    'breaks_even': breaks_even,
                    'win_rate': f'{(wins / num_spins * 100):.1f}%'
                },
                'balance': {
                    'current': float(wallet.balance),
                    'total_deposits': float(wallet.total_deposits),
                    'total_winnings': float(wallet.total_winnings),
                    'total_losses': float(wallet.total_losses)
                },
                'algorithm_used': active_config.name,
                'message': f'Completed {num_spins} spins. Net result: {float(net_result):+.0f} KES'
            }, status=status.HTTP_200_OK)
            
        except ValueError as e:
            return Response(
                {'detail': f'Invalid input: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error performing multi-spin: {str(e)}", exc_info=True)
            return Response(
                {'detail': f'Error performing multi-spin: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def record_spin(self, request):
        """Record a spin result and update wallet balance.
        
        Request body:
        {
            "spin_cost": 20,
            "winnings": 100,
            "multiplier": 5,
            "result_label": "5x"
        }
        
        Returns updated balance and transaction info.
        """
        try:
            from decimal import Decimal
            
            wallet = self.get_game_wallet(request.user)
            
            # Get spin data from request
            spin_cost = Decimal(str(request.data.get('spin_cost', 0)))
            winnings = Decimal(str(request.data.get('winnings', 0)))
            multiplier = request.data.get('multiplier', 0)
            result_label = request.data.get('result_label', 'Unknown')
            
            if spin_cost <= 0:
                return Response(
                    {'detail': 'Spin cost must be positive'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if winnings < 0:
                return Response(
                    {'detail': 'Winnings cannot be negative'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check if user has sufficient balance
            if wallet.balance < spin_cost:
                return Response(
                    {'detail': f'Insufficient balance. Required: {spin_cost}, Available: {wallet.balance}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Deduct spin cost
            wallet.deduct_funds(
                spin_cost,
                reason='spin',
                notes=f'Spin cost for lucky spin game'
            )
            
            # Add winnings (if any)
            if winnings > 0:
                wallet.add_winnings(
                    winnings,
                    game_name='Lucky Spin Wheel',
                    notes=f'Won {result_label} (multiplier {multiplier}x)'
                )
            
            # Return updated balance
            return Response({
                'balance': float(wallet.balance),
                'total_deposits': float(wallet.total_deposits),
                'total_winnings': float(wallet.total_winnings),
                'total_losses': float(wallet.total_losses),
                'spin_cost': float(spin_cost),
                'winnings': float(winnings),
                'net_result': float(winnings - spin_cost),
                'message': f'Spin recorded successfully. Net result: {float(winnings - spin_cost):+.0f}'
            }, status=status.HTTP_200_OK)
            
        except ValueError as e:
            return Response(
                {'detail': f'Invalid input: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error recording spin: {str(e)}", exc_info=True)
            return Response(
                {'detail': f'Error recording spin: {str(e)}'},
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


class SpinAlgorithmViewSet(viewsets.ModelViewSet):
    """API endpoints for managing spin algorithms (admin only)."""
    queryset = SpinAlgorithmConfiguration.objects.all()
    serializer_class = SpinAlgorithmConfigurationSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAdminUser]
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.AllowAny])
    def available(self, request):
        """Get list of all available algorithms (public)."""
        try:
            algorithms = get_all_algorithms()
            return Response({
                'algorithms': algorithms,
                'count': len(algorithms)
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error fetching algorithms: {str(e)}", exc_info=True)
            return Response(
                {'detail': f'Error fetching algorithms: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.AllowAny])
    def active(self, request):
        """Get the currently active algorithm."""
        try:
            active_config = SpinAlgorithmConfiguration.objects.filter(is_active=True).first()
            
            if not active_config:
                return Response({
                    'message': 'No algorithm is currently active',
                    'active': None
                }, status=status.HTTP_200_OK)
            
            serializer = SpinAlgorithmConfigurationSerializer(active_config)
            return Response({
                'active': serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error fetching active algorithm: {str(e)}", exc_info=True)
            return Response(
                {'detail': f'Error fetching active algorithm: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate a specific algorithm configuration."""
        try:
            config = self.get_object()
            config.is_active = True
            config.save()
            
            serializer = SpinAlgorithmConfigurationSerializer(config)
            return Response({
                'message': f'Algorithm "{config.name}" is now active',
                'algorithm': serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error activating algorithm: {str(e)}", exc_info=True)
            return Response(
                {'detail': f'Error activating algorithm: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def all_configurations(self, request):
        """Get all algorithm configurations with their details."""
        try:
            configs = SpinAlgorithmConfiguration.objects.all()
            serializer = SpinAlgorithmConfigurationSerializer(configs, many=True)
            return Response({
                'configurations': serializer.data,
                'count': len(serializer.data)
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error fetching configurations: {str(e)}", exc_info=True)
            return Response(
                {'detail': f'Error fetching configurations: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
