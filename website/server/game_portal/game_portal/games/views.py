import logging

from rest_framework.views import APIView
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from game_portal.accounts.models import Account

from .serializers import GameSerializer
from .models import Game
from .services import get_leaderboard, get_player_stats_for_game


class GameResultSetPagination(PageNumberPagination):
    page_size = 15
    max_page_size = 15
    page_size_query_param = "page_size"


class GameViewSet(viewsets.ModelViewSet):
    queryset = Game.objects.filter(
        game_state__in=[Game.GameState.ACTIVE, Game.GameState.COMING_SOON]
    ).order_by("name")
    serializer_class = GameSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get"]
    pagination_class = GameResultSetPagination


class GameStatsView(APIView):
    permission_classes = [IsAuthenticated]
    http_method_names = ["get"]

    def get(self, request, product_id, format=None):
        data = get_player_stats_for_game(product_id, request.user.id)
        if data is None:
            return Response({'error': 'Could not access the leaderboard server.'})
        return Response(data)


class LeaderboardView(APIView):
    permission_classes = [IsAuthenticated]
    http_method_names = ["get"]

    def get(self, request, product_id, format=None):
        leaderboard_result = get_leaderboard(product_id)
        if leaderboard_result is None:
            return Response({'error': 'Could not access the leaderboard server.'})
        # in_bulk will return a dict of UUID: Account.
        users = {
            str(k): v
            for k, v in Account.objects.in_bulk(
                [e["user_id"] for e in leaderboard_result]
            ).items()
        }

        for entry in leaderboard_result:
            try:
                entry["username"] = users[entry["user_id"]].username
            except:
                logging.warning(
                    f"Unable to process leaderboard user. User Entry: {entry}"
                )
                entry["username"] = "Unknown User"

        return Response(leaderboard_result)
