from concurrent import futures

import google
import grpc
from app.proto.gen import BaseModel1_pb2_grpc, BaseModel1_pb2


class BaseModel1GRPCServiceServicer(BaseModel1_pb2_grpc.BaseModel1GRPCServiceServicer):

    def ExampleCall(self, request, context):
        response = BaseModel1_pb2.ExampleCallResponse(
            transactionsFound=True,
            transactionsCount=42
        )
        return response

    def ExampleCallReturnsEmpty(self, request, context):
        return google.protobuf.empty_pb2.Empty()


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    BaseModel1_pb2_grpc.add_BaseModel1GRPCServiceServicer_to_server(BaseModel1GRPCServiceServicer(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    server.wait_for_termination()


# def start_grpc_server():
#     server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
#     BaseModel1_pb2_grpc.add_BaseModel1GRPCServiceServicer_to_server(BaseModel1GRPCServiceServicer(), server)
#     server.add_insecure_port('[::]:50051')
#     server.start()
#     server.wait_for_termination()


if __name__ == '__main__':
    serve()
