from app.api.v1 import (
    documentRoutes, authRoutes, userRoutes
)

#Authentication
# v1Router.include_router(authRoutes.router, prefix="/auth", tags=["Authentication"])
# v1Router.include_router(documentRoutes.router, prefix="/document/upload", tags=["Document Upload"])
# v1Router.include_router(
#     userRoutes.router,
#     prefix="/user",
#     tags=["Regular User"],
#     dependencies=[Depends(get_current_user)],
# )
# )
# v1Router.include_router(walletRoutes.router, prefix="/wallet", tags=["Wallet"], dependencies=[Depends(get_current_user)],)
# v1Router.include_router(transactionRoutes.router, prefix="/transaction", tags=["Transaction"], dependencies=[Depends(get_current_user)],)
# v1Router.include_router(apiRoutes.router, prefix="/api-keys", tags=["API Keys"], dependencies=[Depends(get_current_user)],)
# v1Router.include_router(paystackRoutes.router, prefix="/payment-gateway", tags=["Payment"])
# v1Router.include_router(
#     adminRoutes.admin_router,
#     prefix="/admin",
#     tags=["Admin"]
# )

# v1Router.include_router(
#     superuserRoutes.super_router,
#     prefix="/superadmin",
#     tags=["SuperAdmin"],
#     dependencies=[Depends(require_superuser)]
# )
# app.include_router(subscription.router, prefix="/api/v1/subscription", tags=["Subscription"], dependencies=[Depends(get_current_user)],)
# app.include_router(ipRoutes.router, prefix="/api/v1/ip", tags=["User IP"])


# v1Router.include_router(authRoutes.router, prefix="/auth", tags=["Authentication"])
# v1Router.include_router(userRoutes.router, prefix="/users", tags=["Users"])
# v1Router.include_router(walletRoutes.router, prefix="/wallets", tags=["Wallets"])
# v1Router.include_router(transactionRoutes.router, prefix="/transactions", tags=["Transactions"])
# v1Router.include_router(apiRoutes.router, prefix="/api-keys", tags=["API Keys"])
# v1Router.include_router(paystackRoutes.router, prefix="/payment", tags=["Payment Gateway"])

# v1Router.include_router(
#     adminRoutes.admin_router,
#     prefix="/admin",
#     tags=["Admin"],
#     dependencies=[Depends(require_admin)]
# )

# v1Router.include_router(
#     superuserRoutes.router,
#     prefix="/superuser",
#     tags=["Superuser"],
#     dependencies=[Depends(require_superuser)]
# )

# v1Router.include_router(reportRoutes.router, prefix="/reports", tags=["Reports"])
# v1Router.include_router(logRoutes.router, prefix="/logs", tags=["System Logs"])
# v1Router.include_router(supportRoutes.router, prefix="/support", tags=["Support"])
# v1Router.include_router(mockapiRoutes.mock_api, prefix="/mock/api", tags=["Mock Api"])