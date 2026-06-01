export const roleAllowedPages = {
  user: ['product_view', 'my_order'],
  manager: ['package_warehouse', 'inventory_warehouse', 'stats'],
  host: [
    'order',
    'stats',
    'category',
    'product',
    'warehouse',
    'inventory',
    'package',
    // 'package_warehouse',
    // 'my_order',
    // 'product_view',
    // 'inventory_warehouse',
    'customer'
  ],
  admin: [
    'order',
    'stats',
    'category',
    'product',
    'warehouse',
    'inventory',
    'package',
    'package_warehouse',
    'my_order',
    'product_view',
    'inventory_warehouse',
    'customer'
  ]
};
