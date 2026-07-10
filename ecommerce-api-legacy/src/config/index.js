const config = {
    port: process.env.PORT || 3000,
    dbUser: process.env.DB_USER || 'admin_master',
    dbPass: process.env.DB_PASS || 'change-me',
    paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY || 'pk_test_placeholder',
    smtpUser: process.env.SMTP_USER || 'no-reply@example.com'
};

module.exports = config;
