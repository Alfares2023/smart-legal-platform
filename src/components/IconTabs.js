import React from 'react';
import { Link } from 'react-router-dom';

function IconTabs() {
  const linkStyle = {
    padding: '10px 20px',
    textDecoration: 'none',
    color: 'white',
    backgroundColor: '#007bff',
    borderRadius: '5px',
    margin: '0 10px'
  };

  const navStyle = {
    display: 'flex',
    justifyContent: 'center',
    padding: '20px',
    backgroundColor: '#343a40'
  };

  return (
    <nav style={navStyle}>
      <Link to="/analysis" style={linkStyle}>تحليل الوثائق</Link>
      <Link to="/generation" style={linkStyle}>إنشاء المستندات</Link>
      <Link to="/pricing" style={linkStyle}>التسعير</Link>
    </nav>
  );
}

export default IconTabs;