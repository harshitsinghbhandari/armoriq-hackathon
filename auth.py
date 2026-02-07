
import logging
from typing import Dict, List, Optional
import time

import requests
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
KEYCLOAK_URL = "http://localhost:8080"
REALM_NAME = "hackathon"
JWKS_URL = f"{KEYCLOAK_URL}/realms/{REALM_NAME}/protocol/openid-connect/certs"
ISSUER = f"{KEYCLOAK_URL}/realms/{REALM_NAME}"
ALGORITHMS = ["RS256"]

# Global cache for JWKS
_jwks_cache: Dict = {}
_jwks_last_fetched: float = 0
JWKS_CACHE_TTL_SECONDS = 300  # 5 minutes

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def get_jwks() -> Dict:
    """
    Fetch JSON Web Key Set (JWKS) from Keycloak with simple in-memory caching.
    """
    global _jwks_cache, _jwks_last_fetched
    current_time = time.time()

    # Return cached keys if valid
    if _jwks_cache and (current_time - _jwks_last_fetched < JWKS_CACHE_TTL_SECONDS):
        return _jwks_cache

    try:
        logger.info(f"Fetching JWKS from {JWKS_URL}")
        response = requests.get(JWKS_URL, timeout=10)
        response.raise_for_status()
        _jwks_cache = response.json()
        _jwks_last_fetched = current_time
        return _jwks_cache
    except requests.RequestException as e:
        logger.error(f"Failed to fetch JWKS: {e}")
        # If we have staled keys, return them as a fallback with a warning
        if _jwks_cache:
            logger.warning("Using stale JWKS cache due to fetch failure")
            return _jwks_cache
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not fetch public keys for validation",
        )


def verify_token(token: str) -> Dict:
    """
    Verify the JWT token signature, expiration, and issuer.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Get the Key ID (kid) from the token header without verification
        unverified_header = jwt.get_unverified_header(token)
        if not unverified_header:
            raise credentials_exception

        kid = unverified_header.get("kid")
        if not kid:
            raise credentials_exception

        # Find the matching key in JWKS
        jwks = get_jwks()
        rsa_key = {}
        for key in jwks.get("keys", []):
            if key.get("kid") == kid:
                rsa_key = {
                    "kty": key["kty"],
                    "kid": key["kid"],
                    "use": key["use"],
                    "n": key["n"],
                    "e": key["e"],
                }
                break
        
        if not rsa_key:
            # Force refresh if key not found (maybe it was rotated)
            # This is a simple improvement to handle rotation edge case
            global _jwks_last_fetched
            _jwks_last_fetched = 0 
            jwks = get_jwks()
            for key in jwks.get("keys", []):
                if key.get("kid") == kid:
                    rsa_key = {
                        "kty": key["kty"],
                        "kid": key["kid"],
                        "use": key["use"],
                        "n": key["n"],
                        "e": key["e"],
                    }
                    break

        if not rsa_key:
            logger.warning(f"Public key not found for kid: {kid}")
            raise credentials_exception

        # Verify the token
        payload = jwt.decode(
            token,
            rsa_key,
            algorithms=ALGORITHMS,
            # We explicitly disable audience verification as it wasn't requested
            # and can be tricky if not configured consistently.
            # Verify audience to prevent token misuse
            audience="account", # Default Keycloak audience for realm users
            issuer=ISSUER
        )
        
        return payload

    except JWTError as e:
        logger.warning(f"JWT verification failed: {e}")
        raise credentials_exception
    except Exception as e:
        logger.error(f"Unexpected error verifying token: {e}")
        raise credentials_exception


async def get_current_user(token: str = Depends(oauth2_scheme)) -> Dict:
    """
    Dependency to get the current user from the Bearer token.
    Returns a dict with 'username' and 'roles'.
    """
    payload = verify_token(token)
    
    # Extract username (prefer 'preferred_username', fallback to 'sub')
    username = payload.get("preferred_username") or payload.get("sub")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token contains no user identity",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Extract realm roles
    realm_access = payload.get("realm_access", {})
    roles = realm_access.get("roles", [])
    
    return {
        "username": username,
        "roles": roles,
    }
