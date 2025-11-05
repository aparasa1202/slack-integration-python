const jwt = require('jsonwebtoken');
const { logInfo, logError } = require('../logger');
const { config } = require('../config');

/**
 * Validates a JWT token
 * @param {string} token - The JWT token to validate
 * @returns {Promise<Object|null>} - The decoded payload if valid, null if invalid
 */
async function validateJWT(token) {
  try {
    if (!token) {
      logError('JWT validation failed: No token provided');
      return null;
    }

    // Remove 'Bearer ' prefix if present
    const cleanToken = token.replace(/^Bearer\s+/i, '');

    if (!config.security.jwtSecret) {
      logError('JWT validation failed: No JWT secret configured');
      return null;
    }

    const decoded = jwt.verify(cleanToken, config.security.jwtSecret);
    logInfo('JWT validation successful', { userId: decoded.userId, exp: decoded.exp });
    
    return decoded;
  } catch (error) {
    if (error.name === 'TokenExpiredError') {
      logError('JWT validation failed: Token expired', { exp: error.expiredAt });
    } else if (error.name === 'JsonWebTokenError') {
      logError('JWT validation failed: Invalid token', { message: error.message });
    } else if (error.name === 'NotBeforeError') {
      logError('JWT validation failed: Token not active', { notBefore: error.date });
    } else {
      logError('JWT validation failed: Unknown error', error);
    }
    return null;
  }
}

/**
 * Generates a JWT token
 * @param {Object} payload - The payload to encode
 * @param {string} expiresIn - Token expiration time
 * @returns {string} - The generated JWT token
 */
function generateJWT(payload, expiresIn = config.security.jwtExpiration) {
  try {
    if (!config.security.jwtSecret) {
      throw new Error('JWT secret not configured');
    }

    const token = jwt.sign(payload, config.security.jwtSecret, { expiresIn });
    logInfo('JWT generated successfully', { userId: payload.userId, expiresIn });
    
    return token;
  } catch (error) {
    logError('JWT generation failed', error);
    throw error;
  }
}

/**
 * Extracts JWT token from request headers
 * @param {Object} headers - Request headers
 * @returns {string|null} - The extracted token or null
 */
function extractTokenFromHeaders(headers) {
  const authorization = headers.authorization || headers.Authorization;
  
  if (!authorization) {
    return null;
  }

  // Handle both 'Bearer token' and just 'token' formats
  if (authorization.startsWith('Bearer ')) {
    return authorization.substring(7);
  }
  
  return authorization;
}

/**
 * Middleware function for validating JWT in Express-like frameworks
 * @param {Object} req - Request object
 * @param {Object} res - Response object
 * @param {Function} next - Next middleware function
 */
async function jwtMiddleware(req, res, next) {
  try {
    const token = extractTokenFromHeaders(req.headers);
    
    if (!token) {
      return res.status(401).json({ error: 'No token provided' });
    }

    const decoded = await validateJWT(token);
    
    if (!decoded) {
      return res.status(401).json({ error: 'Invalid token' });
    }

    req.user = decoded;
    next();
  } catch (error) {
    logError('JWT middleware error', error);
    res.status(500).json({ error: 'Internal server error' });
  }
}

module.exports = {
  validateJWT,
  generateJWT,
  extractTokenFromHeaders,
  jwtMiddleware
};
