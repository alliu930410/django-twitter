from comments.models import Comment
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from comments.api.permissions import IsObjectOwner
from comments.api.serializers import (
    CommentSerializer,
    CommentSerializerForCreate,
    CommentSerializerForUpdate,
)


class CommentViewSet(viewsets.GenericViewSet):
    """
    realize list, create, update, destroy methods
    we do not realize retrieve (check 1 comment) method as there is no such need
    """

    serializer_class = CommentSerializerForCreate
    queryset = Comment.objects.all()
    filterset_fields = ('tweet_id',)

    def get_permissions(self):
        if self.action == 'create':
            return [IsAuthenticated()]
        if self.action in ['destroy', 'update']:
            return [IsAuthenticated(), IsObjectOwner()]
        return [AllowAny()]

    def create(self, request, *args, **kwargs):
        data = {
            'user_id': request.user.id,
            'tweet_id': request.data.get('tweet_id'),
            'content': request.data.get('content'),
        }
        # Note: 'data=' has to be passed in to specify
        # that the params are for data
        # the default first parameter is instance
        serializer = CommentSerializerForCreate(data=data)
        if not serializer.is_valid():
            return Response({
                'message': 'Please check input',
                'errors': serializer.errors,
            }, status=status.HTTP_400_BAD_REQUEST)

        # save will trigger create() method in the serializer
        comment = serializer.save()
        return Response(
            CommentSerializer(comment).data,
            status=status.HTTP_201_CREATED,
        )

    def list(self, request, *args, **kwargs):
        if 'tweet_id' not in request.query_params:
            return Response({
                'message': 'missing tweet_id in request',
                'success': False,
            }, status=status.HTTP_400_BAD_REQUEST)
        queryset = self.get_queryset()
        comments = self.filter_queryset(queryset)\
            .prefetch_related('user').\
            order_by('created_at')
        serializer = CommentSerializer(comments, many=True)
        return Response({
            'comments': serializer.data
        }, status=status.HTTP_200_OK)

    def update(self, request, *args, **kwargs):
        # get_object is a function in DRF package，will raise 404 error when not found
        # so we do not need to have extra logic for not found
        comment = self.get_object()
        serializer = CommentSerializerForUpdate(
            instance=comment,
            data=request.data,
        )
        if not serializer.is_valid():
            return Response({
                'message': 'Please check input',
                'errors': serializer.errors,
            }, status=status.HTTP_400_BAD_REQUEST)
        # save method triggers the update method in serializer
        # save method will decide on whether to trigger create or update based on
        # whether instance parameter is specified or not
        comment = serializer.save()
        return Response(
            CommentSerializer(comment).data,
            status=status.HTTP_200_OK,
        )

    def destroy(self, request, *args, **kwargs):
        comment = self.get_object()
        comment.delete()
        # DRF defaults destroy return value is status code = 204 no content
        # return success=True for FE to use，so return 200 is more appropriate
        return Response({'success': True}, status=status.HTTP_200_OK)