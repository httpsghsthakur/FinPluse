# Finpluse Federated Learning

Ensures absolute privacy by keeping all transaction data on the user's device.

## Protocol
1. Server distributes global model weights (`GET /federated/global_model`).
2. Client trains locally on their private transaction history.
3. Client submits only the *weight updates* back to the server (`POST /federated/submit_update`).
4. Server aggregates updates using FedAvg and begins the next round.
