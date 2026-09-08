// Simple role guard helper used by frontend components
export function hasRole(user, roleName) {
  if (!user) return false;
  if (user.is_staff) return true;
  if (!user.roles) return false;
  return user.roles.includes(roleName);
}
