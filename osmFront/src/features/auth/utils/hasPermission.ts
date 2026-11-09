export function hasPermission(user: any, permission: string) {
    if (!user) return false;
    console.log(user);
    if (user.role.name === 'ADMIN' || user.role.name === 'OWNER') return true;
    return user.permissions.includes(permission);
  }
  
